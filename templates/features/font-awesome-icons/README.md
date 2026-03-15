# Font Awesome Icon Templates

Load this feature-template entrypoint only when
`font-awesome-icons` is enabled in the run capability profile and assigned to
Frontend in the run load plan.

This pack does not replace the core frontend shell wholesale. It layers on top
of the baseline `AppIcon` abstraction.

Expected implementation steps:

1. read `../../../specs/features/font-awesome-icons/README.md`
2. read `../../../specs/features/font-awesome-icons/frontend.md`
3. confirm `runs/current/artifacts/ux/iconography.md` selects Font Awesome
4. adapt `../../app/frontend/AppIcon.tsx.md` to the approved icon mapping
5. add the Font Awesome dependency pins to the generated app

Do not enable this pack by copying icons ad hoc into individual page
templates. The wrapper is the intended swap point.
