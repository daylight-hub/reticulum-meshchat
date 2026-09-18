# Code signing and the Windows download warning

## What the warning actually is

Edge and SmartScreen warn on the installer because the binary has no established
reputation, not because anything was detected in it. The check is on the file's
signature and download history. This matters because it means **no amount of
documentation removes it**: a privacy policy, a disclaimer in the README, or text
inside the app change nothing. Only signing does.

Unsigned builds show "isn't commonly downloaded" or "can't be trusted". Signed
builds accrue reputation and stop warning once enough installs have happened,
with the exception of EV certificates, which start trusted.

## The two routes

| | OV (Organisation Validation) | EV (Extended Validation) |
|---|---|---|
| Cost | roughly $200-400/year | roughly $300-600/year |
| SmartScreen | reputation builds over weeks and hundreds of installs | trusted immediately |
| Key storage | HSM or cloud signing service (required since June 2023) | hardware token or cloud HSM |
| Identity proof | business registration and a verifiable phone listing | the same, plus stricter checks |

Since June 2023 every code signing certificate must have its private key on
certified hardware, so the old "download a .pfx" flow no longer exists for either
type.

## Recommended: Azure Trusted Signing

The cheapest current option and the least painful to automate. Around $10/month,
with the key held in Azure's HSM so there is no token to manage or lose.

1. You need a legal entity — a registered business — with three or more years of
   verifiable history, or Microsoft's identity validation for newer ones.
2. In the Azure portal, create a **Trusted Signing account**, then an **Identity
   Validation** request. Expect a few business days.
3. Create a **Certificate Profile** once validation passes.
4. Give your GitHub Actions workflow an Azure service principal with the
   **Trusted Signing Certificate Profile Signer** role.
5. Add the `azure/trusted-signing-action` step after electron-builder produces
   the artifacts, pointing it at the `.exe` files in `dist/`.
6. Store the credentials as repository secrets. Never commit them.

## The traditional route

If Trusted Signing is not available in your region, buy an OV certificate from
DigiCert, Sectigo or SSL.com. Sectigo is usually cheapest. You will be issued a
cloud HSM account or posted a USB token, and electron-builder can then sign via
the provider's signing tool.

EV is only worth the premium if you cannot tolerate a warning during the
reputation-building window. For a project with a modest download volume, an OV
certificate may take a while to clear the threshold.

## Until it is signed

Be straightforward with users rather than trying to talk them past a security
prompt:

- Publish SHA-256 checksums with every release so a download can be verified.
- Point people at the Actions run that produced the binaries, so the build is
  traceable to a commit.
- Document the click path — More info, then Run anyway — without implying the
  warning is wrong. It is not wrong; the binary genuinely is unsigned.

## What does not work

- Adding a privacy policy or a disclaimer to the README or the app.
- Renaming the installer.
- Submitting the file to Microsoft for reputation reset, without signing first.
- Self-signed certificates. These make SmartScreen warnings worse, not better,
  because the publisher cannot be verified at all.
