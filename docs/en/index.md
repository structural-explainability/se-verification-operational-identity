# SE Paper 210: Operational Identity Verification

> A reference-implementation check for the **finite mathematical core** of
> SE-210, _Operational Identity: A Finite Audit of Declared and Implemented Rules
> of Sameness_.

## Purpose

The purpose of this project is to give executable evidence that
the finite audit of SE-210 is implemented as the paper defines it.
It tests the core once `R`, the declared relation, the surfaces, and the
identified uses are supplied.

It provides evidence, not proof.
Agreement between implementations shows that independent derivations match.
Operation counts show how the fast procedure scales on the histories measured.
Neither certifies the asymptotic bound of the paper's decidability theorem,
and neither replaces the Lean formalization.
