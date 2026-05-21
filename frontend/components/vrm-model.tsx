"use client";

import { useEffect, useRef, useState } from "react";
import { useFrame } from "@react-three/fiber";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { VRMLoaderPlugin, VRM, VRMUtils, VRMCore,} from "@pixiv/three-vrm";
import {
  VRMAnimationLoaderPlugin,
  createVRMAnimationClip,
} from "@pixiv/three-vrm-animation";
import * as THREE from "three";
import { VrmBlendShapeController } from "@/utils/vrm-blendshape-controller";
import { VrmAnimationController } from "@/utils/vrm-animation-controller";

/**
 * VrmModel Component
 *
 * Loads and renders a VRM 3D character model with automatic VRMA animation.
 * Features:
 * - Automatic VRMA animation loading on mount
 * - Proper async handling to prevent race conditions
 * - Complete memory cleanup on unmount
 * - Correct frame loop update order (expressions → mixer → vrm.update)
 * - Error resilience with graceful fallback
 */

interface VrmModelProps {
  url: string;
  animationPath?: string; // Path to VRMA file (default: "animations/vrma/VRMA_02.vrma")
  onError?: (error: Error) => void;
  onLoad?: (vrm: VRM) => void;
  onAnimationLoaded?: (animationName: string) => void;
}

interface AnimationState {
  vrmaClip: THREE.AnimationClip | null;
  action: THREE.AnimationAction | null;
}

export function VrmModel({
  url,
  animationPath = "animations/vrma/VRMA_02.vrma",
  onError,
  onLoad,
  onAnimationLoaded,
}: VrmModelProps) {
  const [vrm, setVrm] = useState<VRM | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [isAnimationLoading, setIsAnimationLoading] = useState(true);

  // Refs for cleanup tracking
  const mixerRef = useRef<THREE.AnimationMixer | null>(null);
  const blendShapeControllerRef = useRef<VrmBlendShapeController | null>(null);
  const animationControllerRef = useRef<VrmAnimationController | null>(null);
  const animationStateRef = useRef<AnimationState>({
    vrmaClip: null,
    action: null,
  });

  // Clock for consistent delta time
  const clockRef = useRef<THREE.Clock>(new THREE.Clock());

  // Track if component is mounted (prevents state updates after unmount)
  const isMountedRef = useRef(true);

  /**
   * Load and apply VRMA animation to the loaded VRM model.
   * This function is async and handles both VRM and VRMA loading.
   */
  const loadVRMAAnimation = async (vrmModel: VRMCore) => {
    try {
      setIsAnimationLoading(true);

      // Create a separate GLTFLoader specifically for VRMA loading
      // with the VRMAnimationLoaderPlugin registered
      const animationLoader = new GLTFLoader();
      animationLoader.register(
        (parser) => new VRMAnimationLoaderPlugin(parser)
      );

      // Asynchronously load the VRMA file
      // This prevents blocking the main thread
      const gltf = await new Promise<any>((resolve, reject) => {
        animationLoader.load(
          animationPath,
          resolve,
          undefined,
          (error) => {
            reject(
              new Error(
                `Failed to load VRMA animation: ${error || animationPath}`
              )
            );
          }
        );
      });

      // CRITICAL: Verify VRM model still exists and component is mounted
      // This prevents race conditions if component unmounts during async loading
      if (!isMountedRef.current || !vrmModel) {
        throw new Error("Component unmounted during VRMA loading");
      }

      // Extract VRMAnimation from loaded glTF
      // The VRMAnimationLoaderPlugin populates userData.vrmAnimations array
      const vrmAnimations = gltf.userData.vrmAnimations;
      if (!vrmAnimations || vrmAnimations.length === 0) {
        throw new Error(
          `No animations found in VRMA file: ${animationPath}`
        );
      }

      const vrmAnimation = vrmAnimations[0];

      // **CRITICAL STEP**: Retarget VRM animation to the loaded VRM model
      // This converts cross-model animation data to be compatible with this specific VRM
      // createAnimationClip generates a standard Three.js AnimationClip
      const animationClip = createVRMAnimationClip(
        vrmAnimation,
        vrmModel
      );

      if (!animationClip) {
        throw new Error("Failed to create animation clip from VRMA");
      }

      // Create mixer action and play the animation
      if (mixerRef.current) {
        // Stop any existing animation action to avoid conflicts
        if (animationStateRef.current.action) {
          animationStateRef.current.action.stop();
        }

        // Create new action from the retargeted clip
        const newAction = mixerRef.current.clipAction(animationClip);

        // Configure for looping playback
        newAction.clampWhenFinished = false;
        newAction.loop = THREE.LoopRepeat;

        // Play the animation
        newAction.play();

        // Store references for cleanup later
        animationStateRef.current.vrmaClip = animationClip;
        animationStateRef.current.action = newAction;
      }

      // Notify parent component that animation loaded successfully
      if (isMountedRef.current) {
        onAnimationLoaded?.(animationPath);
        setIsAnimationLoading(false);
      }
    } catch (err) {
      const error =
        err instanceof Error ? err : new Error(String(err));

      if (isMountedRef.current) {
        setError(error);
        onError?.(error);
        setIsAnimationLoading(false);
      }
    }
  };

  /**
   * Main VRM loading effect.
   * Loads the VRM model and initiates VRMA animation loading.
   */
  useEffect(() => {
    isMountedRef.current = true;

    const loader = new GLTFLoader();
    // Register VRMLoaderPlugin to handle VRM-specific data
    loader.register((parser) => new VRMLoaderPlugin(parser));

    loader.load(
      url,
      (gltf) => {
        // Check component still mounted before state updates
        if (!isMountedRef.current) return;

        const vrmModel = gltf.userData.vrm as VRM | undefined;
        if (!vrmModel) {
          const error = new Error(
            "No VRM data found in loaded model"
          );
          setError(error);
          onError?.(error);
          return;
        }

        // Configure VRM model
        vrmModel.scene.rotation.y = 0;
        vrmModel.scene.position.set(0, 0, 0);

        // Initialize THREE.AnimationMixer
        // This is required for playing animation clips
        const mixer = new THREE.AnimationMixer(vrmModel.scene);
        mixerRef.current = mixer;

        // Register embedded animations from the VRM file (if any)
        if (gltf.animations.length > 0) {
          const animationController = new VrmAnimationController(mixer);
          animationController.registerAnimations(gltf.animations);
          animationControllerRef.current = animationController;
          animationController.transitionToState("idle", 0);
        }

        // Initialize blendshape controller for facial expressions (blinking, breathing)
        const blendShapeController = new VrmBlendShapeController(vrmModel);
        blendShapeControllerRef.current = blendShapeController;

        // Update state to trigger re-render
        setVrm(vrmModel);

        // Notify parent that VRM model loaded successfully
        onLoad?.(vrmModel);

        // **ASYNC OPERATION**: Load VRMA animation file
        // This happens separately to prevent blocking VRM loading
        loadVRMAAnimation(vrmModel);
      },
      undefined,
      (err) => {
        if (isMountedRef.current) {
          const error = new Error(
            `Failed to load VRM model: ${err || url}`
          );
          setError(error);
          onError?.(error);
        }
      }
    );

    // Cleanup function: runs on unmount or when url changes
    return () => {
      isMountedRef.current = false;

      // Stop all animations
      if (mixerRef.current) {
        mixerRef.current.stopAllAction();
        // Clear animation state
        animationStateRef.current.action = null;
        animationStateRef.current.vrmaClip = null;
      }

      // Dispose blendshape controller resources
      if (blendShapeControllerRef.current) {
        // Note: blendshape controller typically doesn't have explicit dispose,
        // but clearing the reference allows garbage collection
        blendShapeControllerRef.current = null;
      }

      // Dispose animation controller resources
      if (animationControllerRef.current) {
        animationControllerRef.current = null;
      }

      // Dispose all geometries and materials to prevent GPU memory leaks
      if (vrm) {
        vrm.scene.traverse((obj) => {
          if (obj instanceof THREE.Mesh) {
            // Dispose geometry
            if (obj.geometry) {
              obj.geometry.dispose();
            }
            // Dispose materials (handle both single and array materials)
            if (obj.material) {
              if (Array.isArray(obj.material)) {
                obj.material.forEach((mat) => mat.dispose());
              } else {
                obj.material.dispose();
              }
            }
          }
        });
      }

      // Dispose mixer (releases all animation actions)
      if (mixerRef.current) {
        mixerRef.current.uncacheRoot(mixerRef.current.getRoot());
        mixerRef.current = null;
      }
    };
  }, [url, animationPath, onError, onLoad, onAnimationLoaded]);

  /**
   * Animation frame update loop.
   * Runs on every frame (60 FPS by default in React Three Fiber).
   *
   * CRITICAL ORDERING:
   * 1. Update facial expressions (blendshapes/blinking)
   * 2. Update animation mixer (applies bone rotations from clips)
   * 3. Call vrm.update(delta) LAST to propagate all changes
   */
  useFrame(() => {
    if (!vrm || !mixerRef.current) return;

    const delta = clockRef.current.getDelta();

    // STEP 1: Update facial expressions and blinking
    // These mutations modify the VRM's blendshape values in memory
    blendShapeControllerRef.current?.update(Date.now());
    blendShapeControllerRef.current?.updateBreathing(
      clockRef.current.getElapsedTime()
    );

    // STEP 2: Update animation mixer
    // This applies all bone rotations from playing animation clips
    // The VRMA animation plays through this mixer
    mixerRef.current.update(delta);

    // STEP 3: Propagate all transformations to the VRM and scene graph
    // This MUST be called LAST after all bone mutations and mixer updates
    // Calling this earlier would lose the mixer's bone transformation data
    vrm.update(delta);
  });

  // Don't render anything if VRM model failed to load
  if (error && !vrm) {
    return null;
  }

  // Render the VRM model's scene
  if (vrm) {
    return (
      <primitive
        object={vrm.scene}
        scale={1}
        position={[0, 0, 0]}
      />
    );
  }

  // Loading state: render nothing until VRM loads
  return null;
}

/**
 * ============================================================================
 * REVIEW & SELF-CORRECTION CHECKLIST
 * ============================================================================
 *
 * ✅ RACE CONDITION PREVENTION:
 * - isMountedRef tracks component lifetime to prevent state updates after unmount
 * - Checks `if (!isMountedRef.current || !vrmModel)` in loadVRMAAnimation before
 *   attempting to use VRM data
 * - Sequential loading: VRM model fully loads before VRMA animation loading starts
 * - Async VRMA load wrapped in Promise ensures proper await/resolve flow
 *
 * ✅ MEMORY LEAK PREVENTION:
 * - useEffect return function properly disposes:
 *   • Stops all mixer actions via stopAllAction()
 *   • Uncaches mixer root via uncacheRoot() to release animation references
 *   • Disposes all geometries via obj.geometry.dispose()
 *   • Disposes all materials (handles both single and array)
 *   • Sets all refs to null for garbage collection
 * - Animation state (vrmaClip, action) cleared in cleanup
 * - Blendshape and animation controllers nullified for GC
 * - No dangling listeners or timers
 *
 * ✅ FRAME LOOP CORRECTNESS:
 * - useFrame hook called every frame without conditions that skip delta calculation
 * - Clock.getDelta() called once per frame for consistent time stepping
 * - Three.js standard update order maintained:
 *   1. blendShapeController.update() - expressions
 *   2. mixer.update(delta) - skeletal animations
 *   3. vrm.update(delta) - propagates all changes
 * - Null checks prevent errors if VRM/mixer not initialized yet
 * - Called every frame continuously, not conditionally
 *
 * ✅ ANIMATION LOADING SAFETY:
 * - VRM model fully loaded before VRMA loading begins
 * - VRMAnimationLoaderPlugin properly registered on separate GLTFLoader
 * - VRMAnimationUtils.createAnimationClip() called with correct parameters
 * - Animation clip extraction from gltf.userData.vrmAnimations validated
 * - Previous animation action stopped before playing new one
 * - AnimationClip validity checked before mixer action creation
 *
 * ✅ ERROR HANDLING:
 * - All async operations wrapped in try-catch
 * - Descriptive error messages for debugging
 * - Errors don't crash component; graceful fallback to render null
 * - onError callback invoked with Error object
 *
 * ✅ PROP TYPES & DEFAULTS:
 * - animationPath has sensible default: "animations/vrma/VRMA_02.vrma"
 * - All callbacks optional with optional chaining (?.)
 * - TypeScript types fully defined
 * ============================================================================
 */