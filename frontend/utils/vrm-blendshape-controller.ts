import { VRM, VRMExpressionPresetName } from "@pixiv/three-vrm";
import * as THREE from "three";
const clock = new THREE.Clock();
interface BlinkConfig {
  minInterval: number;
  maxInterval: number;
  blinkDuration: number;
}

interface BreathingConfig {
  frequency: number;  // Hz (breaths per second, default ~0.19 = ~11 breaths/min)
  amplitude: number;  // 0-1 scale (default 0.01 = 1% chest expansion)
}

const DEFAULT_BLINK_CONFIG: BlinkConfig = {
  minInterval: 2,      // Minimum seconds between blinks
  maxInterval: 5,      // Maximum seconds between blinks
  blinkDuration: 0.15, // Blink animation duration in seconds
};

const DEFAULT_BREATHING_CONFIG: BreathingConfig = {
  frequency: 0.19,  // ~11-12 breaths per minute (natural resting rate)
  amplitude: 0.01,  // 1% chest scale variation (subtle, natural)
};

/**
 * VRM BlendShape (facial expression) controller.
 * Manages natural blinking and other facial expressions via VRM's BlendShapeProxy.
 * Also handles procedural breathing animation for lifelike character movement.
 */
export class VrmBlendShapeController {
  private vrm: VRM;
  private blinkConfig: BlinkConfig;
  private breathingConfig: BreathingConfig;
  private nextBlinkTime: number = 0;
  private isBlinking: boolean = false;
  private blinkStartTime: number = 0;

  constructor(
    vrm: VRM,
    blinkConfig: Partial<BlinkConfig> = {},
    breathingConfig: Partial<BreathingConfig> = {}
  ) {
    this.vrm = vrm;
    this.blinkConfig = { ...DEFAULT_BLINK_CONFIG, ...blinkConfig };
    this.breathingConfig = { ...DEFAULT_BREATHING_CONFIG, ...breathingConfig };
    this.scheduleNextBlink();
  }

  /**
   * Schedule next blink at randomized interval.
   */
  private scheduleNextBlink(): void {
    const randomInterval =
      Math.random() * (this.blinkConfig.maxInterval - this.blinkConfig.minInterval) +
      this.blinkConfig.minInterval;
    this.nextBlinkTime = Date.now() + randomInterval * 1000;
  }

  /**
   * Update blink state. Call this every frame with Date.now() (milliseconds).
   * Returns true if currently blinking.
   */
  public update(currentTime: number): boolean {
    const expressionController = this.vrm.expressionManager;
    if (!expressionController) return false;

    // Trigger blink if interval elapsed
    if (!this.isBlinking && currentTime >= this.nextBlinkTime) {
      this.isBlinking = true;
      this.blinkStartTime = currentTime;
    }

    // Update blink weight based on elapsed time
    if (this.isBlinking) {
      const elapsedBlink = currentTime - this.blinkStartTime;
      // Convert blinkDuration from seconds to milliseconds for correct time scaling
      const blinkDurationMs = this.blinkConfig.blinkDuration * 1000;
      const blinkProgress = Math.min(
        elapsedBlink / blinkDurationMs,
        1
      );

      // Bell curve for natural blink (rise and fall)
      const blinkWeight = Math.sin(blinkProgress * Math.PI);
      expressionController.setValue("blink", blinkWeight);

      // End blink
      if (blinkProgress >= 1) {
        this.isBlinking = false;
        expressionController.setValue("blink", 0);
        this.scheduleNextBlink();
      }
    }

    return this.isBlinking;
  }

  /**
   * Update breathing animation based on elapsed time.
   * Call this every frame with elapsed time in seconds from state.clock.getElapsedTime().
   * Applies subtle chest rotation (pitch) for natural, lifelike character movement.
   * 
   * Uses rotation instead of scale because:
   * - VRM bones are optimized for rotations (quaternion-based)
   * - Weight painting responds more reliably to rotation than scale
   * - Avoids conflicts with skeletal constraints and physics
   */
  public updateBreathing(elapsedTime: number): void {
    if (!this.vrm.humanoid) return;

    // // Get chest bone - the primary bone affected by breathing
    const chest = this.vrm.humanoid.getNormalizedBoneNode("chest");
    if (!chest) return;

    const breathSpeed = 1.2  // Adjust speed by frequency setting
    const breathWave = Math.sin(elapsedTime * breathSpeed);

    // 1. Lấy xương ngực từ hệ thống xương Humanoid của VRM
    // const chest = vrm.humanoid.getNormalizedBoneNode('chest');
    
    if (chest) {
        // Xoay nhẹ trục X của ngực (đơn vị là Radian, 0.05 rad ~ 3 độ)
        // Khi thở vào ngực hơi ưỡn lên, thở ra ngực hạ xuống
        chest.rotation.x = breathWave * 0.04; 
    }

    // 2. Nếu muốn cả người nhấp nhô lên xuống nhẹ theo nhịp thở
    // Tác động vào xương Hông (Hips) - xương gốc của toàn bộ cơ thể
    const hips = this.vrm.humanoid.getNormalizedBoneNode('hips');
    if (hips) {
        // Nhấp nhô cực kỳ nhẹ để không bị cảm giác nhân vật đang nhảy
        hips.position.y = breathWave * 0.004; 
    }

    // Cập nhật trạng thái VRM trước khi render để đảm bảo mọi thay đổi về biểu cảm và xương được áp dụng lên GPU
    this.vrm.update(clock.getDelta());
  }
  public setExpression(
    expressionName: VRMExpressionPresetName,
    value: number
  ): void {
    const expressionController = this.vrm.expressionManager;
    if (expressionController) {
      expressionController.setValue(expressionName, Math.max(0, Math.min(1, value)));
    }
  }

  /**
   * Get current expression value.
   */
  public getExpression(expressionName: VRMExpressionPresetName): number {
    const expressionController = this.vrm.expressionManager;
    return expressionController?.getValue(expressionName) ?? 0;
  }

  /**
   * Reset all expressions to zero.
   */
  public resetExpressions(): void {
    const expressionController = this.vrm.expressionManager;
    if (expressionController) {
      // Reset common VRM expression presets
      const presets: VRMExpressionPresetName[] = [
        "blink",
        "blinkLeft",
        "blinkRight",
        "lookUp",
        "lookDown",
        "lookLeft",
        "lookRight",
        "happy",
        "sad",
        "angry",
        "surprised",
        "relaxed",
        "neutral",
      ];
      presets.forEach((preset) => {
        expressionController.setValue(preset, 0);
      });
    }
  }
}