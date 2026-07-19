# Source provenance

## Public RP-R4 implementation

RP-R4 was created as a new repository implementation from the functional requirements validated during the private RP-R1 to RP-R3 prototypes.

The public baseline was deliberately rebuilt with:

- a new `src/` package architecture;
- a new local API and session model;
- a new project registry and legacy metadata importer;
- a new profile schema;
- a new preflight engine;
- new Windows and Android builders;
- a new interface written for Rubra Packager;
- newly written documentation and tests;
- no inherited images or logo files.

## Historical inspiration

The original HTML2EXE repository supplied by the user was used to understand the broad workflow of wrapping static web content with PyWebView/PyInstaller and Capacitor. It did not provide an explicit license file in the supplied snapshot.

For that reason, the public RP-R4 tree does not publish the original repository as a fork and does not carry its Git history or UI assets. The historical relationship is acknowledged here rather than hidden.

## Verification rule

Before a public release, compare the candidate tree against the supplied original snapshot and investigate any substantial identical blocks. Functional similarity alone is expected; copied expressive source is not.
