# Motion Animations Activation

Enable this pack only when the run explicitly needs:

- layout transitions
- gesture interactions
- animation choreography beyond basic CSS transitions
- scroll-based reveal behavior

This pack MUST NOT be enabled for cosmetic animation alone.

Install pin:

- `motion@12.36.0`

Rules:

- use `motion`, not `framer-motion`
- import React bindings from `motion/react`
- document reduced-motion behavior in the run-owned UX artifacts
