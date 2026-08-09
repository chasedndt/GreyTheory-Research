# GitLab HackerOne programme guidelines — operator extract

- Source: https://hackerone.com/gitlab?type=team
- Source update date shown: 2026-07-21
- Retrieved: 2026-08-09T10:30:00Z
- Capture mode: operator_extract

Authority facts retained for compilation:

1. The programme adopts HackerOne Core Ineligible Findings and documents a platform-standard deviation for self-sign-up severity scoring.
2. Testing that may expose other users' private information must use only controlled test accounts.
3. Researchers must not test projects, groups, accounts, or instances they do not own.
4. Disruptive activity, spam-like or high-volume activity, and unverified automated-tool reports are prohibited.
5. Denial-of-service testing must never be performed on GitLab.com.
6. Local GitLab Development Kit or self-managed instances are the preferred research surface for most vulnerability work.
7. Testing on GitLab.com requires an account associated with the researcher's HackerOne email alias.
8. Third-party services on GitLab subdomains are strictly out of scope.
9. Scope-table inclusions and exclusions qualify the general statement that GitLab products are in scope.
10. The public page does not state a numeric request rate for target interaction.

Compilation decision for this saved bundle:

- Preserve every executable scope-table row as written.
- Apply explicit out-of-scope rows before broader in-scope wildcards.
- Compile only `LOCAL_FIXTURE` authority because no live-operation rate is stated and the GreyTheory posture has not been raised.
- Do not treat the bundle as human-reviewed.

This is a bounded, paraphrased authority extract. It is not the complete page.
