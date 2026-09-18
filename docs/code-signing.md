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

## There is no longer any way to remove the warning immediately

This changed in 2024 and most of the internet has not caught up. Microsoft's own
documentation now states that EV certificates no longer bypass SmartScreen, that
all code signing certificates are treated equally, and that paying a premium for
EV solely to avoid SmartScreen warnings is no longer justified. Resellers still
advertise "instant SmartScreen trust" for EV. That claim is out of date.

Reputation is now earned by download volume, for both OV and EV, and it attaches
to the certificate thumbprint **and** the file hash. Every new build starts its
file-hash reputation from zero and inherits the publisher reputation of the
certificate that signed it.

The one exception: applications distributed through the Microsoft Store are
re-signed by Microsoft and carry full reputation, so Store-installed apps never
show the warning.

## Self-signed certificates do not work

A certificate you generate yourself is not chained to a trusted root, so Windows
cannot verify the publisher at all. This makes the warnings worse, not better,
and adds a second complaint about an untrusted issuer. Signing is only useful
with a certificate from a CA in the Microsoft Trusted Root Program.

## What a company under three years old can get

| | Azure Artifact Signing | OV from a commercial CA | EV from a commercial CA |
|---|---|---|---|
| Company under 3 years | **not eligible** | yes | yes |
| Region limits | US and Canada only | none | none |
| Cost | from about $10/month | roughly $200-400/yr | roughly $280-600/yr |
| SmartScreen | builds over time | builds over time | builds over time |
| Kernel drivers | no | no | yes |

Microsoft requires three or more years of verifiable organisational history for
Artifact Signing (formerly Trusted Signing), with **no exception path** and no
manual override, and it is limited to organisations registered in the US or
Canada. A company under a year old cannot use it yet.

Commercial CAs have no such age rule. A newly registered company can obtain OV,
or EV, by providing registration documents, a verifiable phone listing, and
sometimes a legal or accountant's letter. Sectigo and SSL.com are usually the
cheapest.

Given that EV no longer helps with SmartScreen, **OV is the sensible purchase**
unless you need kernel-mode driver signing or an enterprise customer's
procurement demands EV.

Since June 2023 the private key for any publicly trusted code signing
certificate must live on certified hardware, so the old downloadable `.pfx`
workflow no longer exists for either type. You will get a cloud HSM account or a
posted USB token.

## If you stop paying

**Existing releases keep working, provided you timestamped them.** A timestamped
signature remains valid indefinitely after the certificate expires, because the
timestamp proves the signing happened while the certificate was live. Always
timestamp. Without it, signatures fail the moment the certificate lapses.

What you lose is the ability to sign anything new. Unsigned builds you publish
after that point start from zero reputation again.

**You can restart later**, but reputation does not come back with you.
Reputation is tied to the certificate thumbprint, so a new certificate begins at
zero — this is true even of a straight renewal from the same CA under the same
company name, which catches people out regularly. Teams that ship continuously
dual-sign during the overlap window so the new certificate accumulates
reputation before the old one lapses. If you let a certificate lapse entirely,
budget for a fresh reputation-building period when you return.

**None of this affects your ability to publish a release.** Signing is not
required to build, tag, or distribute anything. GitHub Releases, your Docker
image and the installers all work unsigned. The only difference is the warning.

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
