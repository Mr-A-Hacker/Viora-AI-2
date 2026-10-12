# Viora AI 2 — Project Roadmap

This roadmap is a set of possible next steps for Viora AI 2. It is not a statement that every item is already available.

## Interface and accessibility
- [ ] Add a guided first-run setup for models, microphone, speakers, and camera.
- [ ] Improve keyboard navigation and visible focus states.
- [ ] Add a compact mode for smaller screens and Raspberry Pi displays.
- [ ] Provide consistent loading, empty, and error states across tools.

## Local AI and tools
- [ ] Show model download status, disk-space needs, and model readiness.
- [ ] Add a diagnostics screen for missing dependencies and unavailable hardware.
- [ ] Let users configure resource limits for lower-powered devices.
- [ ] Make online-dependent features visibly distinct from offline features.

## Privacy and safety
- [ ] Make microphone/camera activity and permission state obvious.
- [ ] Add simple controls to export and delete local conversation or gallery data.
- [ ] Avoid logging prompts, credentials, or private captured media by default.
- [ ] Document data storage locations and how to clear them.

## Quality
- [ ] Add automated tests for configuration parsing and core utilities.
- [ ] Document a repeatable clean-install procedure for Raspberry Pi and Linux.
- [ ] Test graceful behavior when models, audio devices, or the network are unavailable.
- [ ] Keep feature claims aligned with the current implementation.
