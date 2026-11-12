from panda_md import SlitPore, synthetic_profile

pore = SlitPore(width_nm=8.0, length_nm=16.0)
roll = pore.interface("roll")
truth = {"theta": 120.0, "delta": 0.03, "phi": 0.40}
profile = synthetic_profile(
    roll, truth, density_bulk_per_nm3=30.0,
    noise_std=0.005, seed=0,
)
result = roll.fit(
    profile, optimize=["theta", "delta"], density_bulk_per_nm3=30.0,
)
print(f"theta = {result.values['theta']:.2f} deg")
print(f"delta/H = {result.values['delta']:.4f}")
print(f"phi = {result.values['phi']:.4f}")
print(f"L1 loss = {result.loss:.5f}")
print(result.problems())
