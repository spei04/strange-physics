# Related work and positioning

This is an initial positioning review, not an exhaustive novelty assessment.

| Project | Relevant overlap | Consequence for this project |
| --- | --- | --- |
| [DiscoveryWorld](https://github.com/allenai/discoveryworld) | Interactive environments for automated scientific discovery | Cite it as a broader environment; keep the first release focused on numerical identification. |
| [DiscoverPhysics](https://arxiv.org/abs/2605.26087) / [code](https://github.com/SampsonML/DiscoverPhysics) | Unfamiliar simulated force laws, active experiments, raw trajectories, held-out trajectory scoring, and time-varying interactions | Strange physics and changing interactions alone are not a novelty claim. Focus on unannounced regime changes, false alarms, recovery curves and controlled comparisons. |
| [PhysGym](https://github.com/principia-ai/PhysGym) | Controlled prior information and interactive equation discovery | Disclose the feature library and agent-visible metadata; separate restricted model fitting from open-ended discovery. |
| [PySINDy](https://github.com/dynamicslab/pysindy) | Sparse identification of nonlinear dynamics | Use established identification ideas and compare against competent numerical baselines. Decide on the dependency after prototyping the small initial dictionary. |

The working contribution is a tightly measured adaptation benchmark with visual
inspection, not a claim to have invented physics-discovery environments. Before
a paper or novelty claim, extend this review to change-point detection, adaptive
system identification, active learning under drift, and continual learning.

Links above are references; no upstream source code or assets are copied into
this repository. No simulator or benchmark code has been implemented yet.
