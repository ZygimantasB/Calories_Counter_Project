import { describe, it, expect } from 'vitest';

describe('API selector environment fallback', () => {
  it('loads offline APIs when running inside the Vitest test environment (MODE=test)', async () => {
    const { foodApi } = await import('../food');
    const { default: foodOffline } = await import('../food.offline');
    expect(foodApi).toBe(foodOffline);
  });

  it('loads offline settings API by default in test mode', async () => {
    const { settingsApi } = await import('../settings');
    const { default: settingsOffline } = await import('../settings.offline');
    expect(settingsApi).toBe(settingsOffline);
  });

  it('loads offline running API by default in test mode', async () => {
    const { runningApi } = await import('../running');
    const { default: runningOffline } = await import('../running.offline');
    expect(runningApi).toBe(runningOffline);
  });

  it('loads offline workout API by default in test mode', async () => {
    const { workoutApi } = await import('../workout');
    const { default: workoutOffline } = await import('../workout.offline');
    expect(workoutApi).toBe(workoutOffline);
  });

  it('loads offline weight API by default in test mode', async () => {
    const { weightApi } = await import('../weight');
    const { default: weightOffline } = await import('../weight.offline');
    expect(weightApi).toBe(weightOffline);
  });

  it('loads offline bodyMeasurements API by default in test mode', async () => {
    const { bodyMeasurementsApi } = await import('../bodyMeasurements');
    const { default: bodyMeasurementsOffline } = await import('../bodyMeasurements.offline');
    expect(bodyMeasurementsApi).toBe(bodyMeasurementsOffline);
  });

  it('loads offline analytics API by default in test mode', async () => {
    const { analyticsApi } = await import('../analytics');
    const { default: analyticsOffline } = await import('../analytics.offline');
    expect(analyticsApi).toBe(analyticsOffline);
  });

  it('loads offline mealTemplates API by default in test mode', async () => {
    const { mealTemplatesApi } = await import('../mealTemplates');
    const { default: mealTemplatesOffline } = await import('../mealTemplates.offline');
    expect(mealTemplatesApi).toBe(mealTemplatesOffline);
  });
});
