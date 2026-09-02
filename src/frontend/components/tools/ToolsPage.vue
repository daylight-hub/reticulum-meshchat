<template>
    <div class="flex flex-col flex-1 overflow-hidden min-w-full sm:min-w-[500px] dark:bg-zinc-950">
        <div class="overflow-y-auto space-y-2 p-2">

            <!-- appearance -->
            <div class="bg-white dark:bg-zinc-800 rounded shadow">
                <div class="flex border-b border-gray-300 dark:border-zinc-700 text-gray-700 dark:text-gray-200 p-2 font-semibold">Tools</div>
                <div class="dark:divide-zinc-700 text-gray-900 dark:text-gray-100 p-2">
                    A collection of useful tools bundled with LCS MeshChat
                </div>
            </div>

            <!-- ping -->
            <RouterLink :to="{ name: 'ping' }" class="group flex bg-white dark:bg-zinc-800 p-2 rounded shadow hover:bg-gray-50 dark:hover:bg-zinc-700">
                <div class="mr-2">
                    <div class="flex bg-gray-300 text-gray-500 rounded shadow p-2">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="size-10">
                            <path fill-rule="evenodd" d="M14.615 1.595a.75.75 0 0 1 .359.852L12.982 9.75h7.268a.75.75 0 0 1 .548 1.262l-10.5 11.25a.75.75 0 0 1-1.272-.71l1.992-7.302H3.75a.75.75 0 0 1-.548-1.262l10.5-11.25a.75.75 0 0 1 .913-.143Z" clip-rule="evenodd" />
                        </svg>
                    </div>
                </div>
                <div class="my-auto mr-auto dark:text-gray-200">
                    <div class="font-bold">Ping</div>
                    <div class="text-sm">Allows you to ping a destination hash.</div>
                </div>
                <div class="my-auto text-gray-400 group-hover:text-gray-500">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-6">
                        <path stroke-linecap="round" stroke-linejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5"></path>
                    </svg>
                </div>
            </RouterLink>

            <!-- rnode configuration tool (LCS) -->
            <a target="_blank" href="/rnode-config/index.html" class="group flex bg-white dark:bg-zinc-800 p-2 rounded shadow hover:bg-gray-50 dark:hover:bg-zinc-700">
                <div class="mr-2">
                    <div class="flex items-center justify-center size-14 rounded shadow bg-gradient-to-br from-[#1e5aa0] to-[#123a6b] p-1">
                        <img class="w-full h-full object-contain" src="/assets/images/lcs-logo.png" alt="Liberty Communication Systems" />
                    </div>
                </div>
                <div class="my-auto mr-auto dark:text-gray-200">
                    <div class="font-bold">RNode Configuration Tool</div>
                    <div class="text-sm">Flash and configure RNode LoRa radios.</div>
                </div>
                <div class="my-auto text-gray-400 group-hover:text-gray-500">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-6">
                        <path stroke-linecap="round" stroke-linejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5"></path>
                    </svg>
                </div>
            </a>

            <!-- transport node console -->
            <a target="_blank" href="/transport-console/index.html" class="group flex bg-white dark:bg-zinc-800 p-2 rounded shadow hover:bg-gray-50 dark:hover:bg-zinc-700">
                <div class="mr-2">
                    <div class="flex items-center justify-center size-14 rounded shadow text-white bg-gradient-to-br from-[#1e5aa0] to-[#123a6b]">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-8">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M6.75 7.5l3 2.25-3 2.25m4.5 0h3m-9 8.25h13.5A2.25 2.25 0 0021 18V6a2.25 2.25 0 00-2.25-2.25H5.25A2.25 2.25 0 003 6v12a2.25 2.25 0 002.25 2.25z" />
                        </svg>
                    </div>
                </div>
                <div class="my-auto mr-auto dark:text-gray-200">
                    <div class="font-bold">Transport Node Console</div>
                    <div class="text-sm">Configure and monitor RNode transport nodes.</div>
                </div>
                <div class="my-auto text-gray-400 group-hover:text-gray-500">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-6">
                        <path stroke-linecap="round" stroke-linejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5"></path>
                    </svg>
                </div>
            </a>

            <!-- read the holy bible (bundled KJV pdf) -->
            <a target="_blank" href="/bible/KJV-Bible.pdf" class="group flex bg-white dark:bg-zinc-800 p-2 rounded shadow hover:bg-gray-50 dark:hover:bg-zinc-700">
                <div class="mr-2">
                    <div class="flex items-center justify-center size-14 rounded shadow text-white bg-gradient-to-br from-[#1e5aa0] to-[#123a6b]">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-8">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25" />
                        </svg>
                    </div>
                </div>
                <div class="my-auto mr-auto dark:text-gray-200">
                    <div class="font-bold">Read the Holy Bible</div>
                    <div class="text-sm">King James Version &middot; available offline.</div>
                </div>
                <div class="my-auto text-gray-400 group-hover:text-gray-500">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-6">
                        <path stroke-linecap="round" stroke-linejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5"></path>
                    </svg>
                </div>
            </a>

            <!-- about reticulum - in-app LCS Network guide (LCS) -->
            <button type="button" @click="showGuide = true" class="text-left w-full group flex bg-white dark:bg-zinc-800 p-2 rounded shadow hover:bg-gray-50 dark:hover:bg-zinc-700">
                <div class="mr-2">
                    <div class="flex items-center justify-center size-14 rounded shadow bg-white p-1">
                        <img class="w-full h-full object-contain" src="/assets/images/reticulum_logo_512.png" alt="Reticulum" />
                    </div>
                </div>
                <div class="my-auto mr-auto dark:text-gray-200">
                    <div class="font-bold">About Reticulum</div>
                    <div class="text-sm">The LCS Network guide to Reticulum, LXMF and LXST.</div>
                </div>
                <div class="my-auto text-gray-400 group-hover:text-gray-500">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-6">
                        <path stroke-linecap="round" stroke-linejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5"></path>
                    </svg>
                </div>
            </button>

            <!-- purchase rnode mesh radios (LCS) -->
            <a target="_blank" href="https://lcs.network" class="group flex bg-white dark:bg-zinc-800 p-2 rounded shadow hover:bg-gray-50 dark:hover:bg-zinc-700">
                <div class="mr-2">
                    <div class="flex items-center justify-center size-14 rounded shadow text-white bg-gradient-to-br from-[#1e5aa0] to-[#123a6b]">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-8">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 3h1.386c.51 0 .955.343 1.087.835l.383 1.437M7.5 14.25a3 3 0 0 0-3 3h15.75m-12.75-3h11.218c1.121-2.3 2.1-4.684 2.924-7.138a60.114 60.114 0 0 0-16.536-1.84M7.5 14.25 5.106 5.272M6 20.25a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0Zm12.75 0a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0Z" />
                        </svg>
                    </div>
                </div>
                <div class="my-auto mr-auto dark:text-gray-200">
                    <div class="font-bold">Purchase RNode Mesh Radios</div>
                    <div class="text-sm">lcs.network</div>
                </div>
                <div class="my-auto text-gray-400 group-hover:text-gray-500">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-6">
                        <path stroke-linecap="round" stroke-linejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5"></path>
                    </svg>
                </div>
            </a>

        </div>

        <!-- LCS: About Reticulum - the LCS Network guide, in-app -->
        <div v-if="showGuide" @click.self="showGuide = false" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
            <div class="bg-white dark:bg-zinc-900 rounded-lg shadow-xl max-w-4xl w-full max-h-[88vh] flex flex-col">

                <div class="flex items-center justify-between p-4 border-b dark:border-zinc-700">
                    <div class="flex items-center gap-x-3">
                        <img class="size-9 object-contain" src="/assets/images/reticulum_logo_512.png" alt="Reticulum" />
                        <div>
                            <h2 class="text-lg font-bold dark:text-white leading-tight">The LCS Network</h2>
                            <div class="text-xs text-gray-500 dark:text-gray-400">A Guide to Reticulum, LXMF and LXST</div>
                        </div>
                    </div>
                    <button type="button" @click="showGuide = false" class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-6">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                <div class="overflow-y-auto p-5 space-y-6 text-sm dark:text-gray-200 leading-relaxed">

                    <p class="text-gray-600 dark:text-gray-300">
                        This explains what the LCS Network is, how it works, and what it requires. It is
                        written for someone who has never encountered Reticulum before, and applies to
                        <b>Liberty Chat</b>, <b>LCS MeshChat</b>, and the <b>Liberty Deck</b>.
                    </p>

                    <!-- 1. three layer stack -->
                    <section>
                        <h3 class="font-bold text-base mb-2 text-blue-700 dark:text-blue-400">1. The Three-Layer Stack</h3>
                        <p class="mb-2">The LCS Network runs three open protocols, each handling one job.</p>
                        <div class="overflow-x-auto">
                            <table class="w-full text-xs border dark:border-zinc-700">
                                <thead class="bg-gray-100 dark:bg-zinc-800">
                                    <tr>
                                        <th class="text-left p-2 border dark:border-zinc-700">Layer</th>
                                        <th class="text-left p-2 border dark:border-zinc-700">Protocol</th>
                                        <th class="text-left p-2 border dark:border-zinc-700">Function</th>
                                        <th class="text-left p-2 border dark:border-zinc-700">Analogy</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr><td class="p-2 border dark:border-zinc-700 font-medium">Bottom</td><td class="p-2 border dark:border-zinc-700">Reticulum (RNS)</td><td class="p-2 border dark:border-zinc-700">Addressing, routing and encryption across any physical medium.</td><td class="p-2 border dark:border-zinc-700">The road network</td></tr>
                                    <tr><td class="p-2 border dark:border-zinc-700 font-medium">Middle</td><td class="p-2 border dark:border-zinc-700">LXMF</td><td class="p-2 border dark:border-zinc-700">Text, files, images and recorded voice — with store-and-forward delivery for offline recipients.</td><td class="p-2 border dark:border-zinc-700">The postal service</td></tr>
                                    <tr><td class="p-2 border dark:border-zinc-700 font-medium">Top</td><td class="p-2 border dark:border-zinc-700">LXST</td><td class="p-2 border dark:border-zinc-700">Live, encrypted voice calls.</td><td class="p-2 border dark:border-zinc-700">The telephone</td></tr>
                                </tbody>
                            </table>
                        </div>
                        <ul class="list-disc ml-5 mt-2 space-y-1">
                            <li>Reticulum is the foundation. LXMF and LXST ride on top of it and inherit its encryption and routing automatically.</li>
                            <li>All three LCS apps are <b>LXMF clients</b>. They interoperate fully, including with third-party clients such as Sideband and Nomad Network.</li>
                        </ul>
                    </section>

                    <!-- 2. reticulum -->
                    <section>
                        <h3 class="font-bold text-base mb-2 text-blue-700 dark:text-blue-400">2. Reticulum — The Network Foundation</h3>
                        <p class="mb-2">
                            Reticulum is an open-source, cryptography-based networking stack built for links that
                            are slow, intermittent and untrusted. It does not assume servers, providers or fixed
                            infrastructure. It was built by Mark Qvist.
                        </p>
                        <ul class="list-disc ml-5 space-y-1">
                            <li><b>No central authority.</b> No registry, no account server, no gatekeeper.</li>
                            <li><b>No addresses or ports.</b> A single concept — a <i>destination</i> — derived from cryptographic keys. No DHCP, subnetting or port forwarding.</li>
                            <li><b>Medium-agnostic.</b> The same packets travel over LoRa, packet radio, Wi-Fi, Ethernet, USB, Bluetooth or the internet, mixed freely in one network.</li>
                            <li><b>Encrypted by default.</b> Encryption is structural, not optional. Unencrypted traffic cannot be forwarded across multiple hops.</li>
                            <li><b>Extreme bandwidth tolerance.</b> Remains functional on links as slow as 5 bits per second.</li>
                            <li><b>Location-independent addresses.</b> A device keeps the same address on home Wi-Fi, a LoRa radio or the public internet.</li>
                        </ul>
                        <p class="mt-2 border-l-4 border-amber-500 pl-3 text-gray-600 dark:text-gray-300">
                            An RNode radio without a host is just a radio. A host without an interface cannot reach
                            anyone. Together they form a node on the network.
                        </p>
                    </section>

                    <!-- 3. instances nodes interfaces -->
                    <section>
                        <h3 class="font-bold text-base mb-2 text-blue-700 dark:text-blue-400">3. Instances, Nodes and Interfaces</h3>
                        <p class="mb-2"><b>Instance</b> — every host device running Reticulum. It simply means "Reticulum is running here."</p>
                        <p class="mb-1"><b>Node</b> — an instance given a specific role:</p>
                        <ul class="list-disc ml-5 space-y-1 mb-2">
                            <li><b>Client node</b> — an endpoint. Sends and receives for a user, does not relay. This is the default.</li>
                            <li><b>Transport node</b> — a relay. Forwards others' encrypted traffic one hop closer, and cannot read it. Enabled with <code>enable_transport = Yes</code>.</li>
                            <li><b>Propagation node</b> — a store-and-forward mailbox for offline recipients.</li>
                        </ul>
                        <p><b>Interface</b> — the connection between the host and the physical medium. It is not a node; it is the on-ramp a node uses. One host can run several at once, and Reticulum picks among them automatically.</p>
                    </section>

                    <!-- 4. identities -->
                    <section>
                        <h3 class="font-bold text-base mb-2 text-blue-700 dark:text-blue-400">4. Identities and Addresses</h3>
                        <p class="mb-2">
                            A <b>Reticulum Identity</b> is a public/private key pair generated locally at first
                            launch. No registration, phone number or email is required. The private key stays on
                            the device; the public key lets others encrypt traffic only you can open.
                        </p>
                        <p class="mb-2">
                            An <b>LXMF address</b> is derived from that identity — a 32-character hex hash such as
                            <code class="text-xs">13425ec15b621c1d928589718000d814</code>. No registrar issues it, no
                            authority can revoke it, and it cannot be impersonated.
                        </p>
                        <p class="border-l-4 border-red-500 pl-3 text-gray-600 dark:text-gray-300">
                            Back up the identity file and treat it like a private key. Whoever holds it controls
                            that address.
                        </p>
                    </section>

                    <!-- 5. announces -->
                    <section>
                        <h3 class="font-bold text-base mb-2 text-blue-700 dark:text-blue-400">5. The Announce System</h3>
                        <p class="mb-2">Reticulum has no directory server. Peers are discovered through <b>announces</b> — small signed broadcasts carrying the address, public key, an optional display name and an Ed25519 signature.</p>
                        <ul class="list-disc ml-5 space-y-1">
                            <li>A device that has never announced is not reachable. Press <b>Announce</b> once at setup.</li>
                            <li>Announcing makes your display name appear in others' peer lists automatically.</li>
                            <li>Re-announce after any change in how you connect — switching interfaces, attaching or removing an RNode, or joining a different network.</li>
                            <li>Announce sparingly. Flooding causes the network to down-prioritize you, making you <i>harder</i> to reach.</li>
                            <li>Announces stop after 128 hops and are capped at 2% of interface bandwidth, so a fast network cannot flood a slow LoRa segment.</li>
                        </ul>
                    </section>

                    <!-- 6. LXMF -->
                    <section>
                        <h3 class="font-bold text-base mb-2 text-blue-700 dark:text-blue-400">6. LXMF — Messaging</h3>
                        <ul class="list-disc ml-5 space-y-1">
                            <li>Protocol overhead is only 111 bytes per message — small enough for LoRa and packet radio.</li>
                            <li>Every message is timestamped and Ed25519-signed, so the sender cannot be forged.</li>
                            <li>Messages carry a title, body and an extensible fields section for attachments, images, audio clips, location and telemetry.</li>
                            <li><b>Propagation nodes</b> hold messages for offline recipients and deliver them on reconnection. They peer and synchronize with each other, with no single point of failure — and they store messages they cannot read.</li>
                        </ul>
                    </section>

                    <!-- 7. LXST -->
                    <section>
                        <h3 class="font-bold text-base mb-2 text-blue-700 dark:text-blue-400">7. LXST — Real-Time Voice</h3>
                        <div class="overflow-x-auto mb-2">
                            <table class="w-full text-xs border dark:border-zinc-700">
                                <thead class="bg-gray-100 dark:bg-zinc-800">
                                    <tr>
                                        <th class="text-left p-2 border dark:border-zinc-700">Codec</th>
                                        <th class="text-left p-2 border dark:border-zinc-700">Bit rate</th>
                                        <th class="text-left p-2 border dark:border-zinc-700">Suited to</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr><td class="p-2 border dark:border-zinc-700">Codec2</td><td class="p-2 border dark:border-zinc-700">700 – 3,200 bps</td><td class="p-2 border dark:border-zinc-700">LoRa and packet radio — intelligible speech at minimal bandwidth</td></tr>
                                    <tr><td class="p-2 border dark:border-zinc-700">Opus</td><td class="p-2 border dark:border-zinc-700">~4.5 – 96 kbps</td><td class="p-2 border dark:border-zinc-700">Wi-Fi, Ethernet and internet — natural, high-quality voice</td></tr>
                                </tbody>
                            </table>
                        </div>
                        <ul class="list-disc ml-5 space-y-1">
                            <li>Codecs can be switched mid-call without dropping the call, and the change is signalled to the remote end.</li>
                            <li>Live calls need a fast LoRa preset — <b>Short Fast</b> (≈10.9 kbps) is the slowest that can carry one. <b>Half-duplex</b> mode is recommended on slow links.</li>
                            <li><b>Long Fast</b> (≈1.07 kbps) is the general-purpose preset for text and PTT, but cannot sustain a live call.</li>
                            <li>Where the link is too slow, use push-to-talk voice clips instead — recorded and sent as LXMF messages, which work on any link.</li>
                        </ul>
                    </section>

                    <!-- 8. transport modes -->
                    <section>
                        <h3 class="font-bold text-base mb-2 text-blue-700 dark:text-blue-400">8. Transport Modes</h3>
                        <ul class="list-disc ml-5 space-y-1">
                            <li><b>full</b> — default. All discovery, meshing and transport active. Client devices and most links.</li>
                            <li><b>gateway</b> — also resolves unknown paths for devices behind it. The LAN-facing interface of a gateway.</li>
                            <li><b>access_point</b> — quiet until used: no automatic announces, short-lived paths.</li>
                            <li><b>roaming</b> — marks a physically mobile interface.</li>
                            <li><b>boundary</b> — marks a transition to a very different segment, e.g. the internet side of a gateway whose local side is LoRa.</li>
                        </ul>
                        <p class="mt-2 text-gray-600 dark:text-gray-300">Transport is disabled by default — client apps do not relay other users' traffic.</p>
                    </section>

                    <!-- 9. security -->
                    <section>
                        <h3 class="font-bold text-base mb-2 text-blue-700 dark:text-blue-400">9. Security</h3>
                        <p class="mb-2">LXMF and LXST implement no separate cryptography — both inherit Reticulum's:</p>
                        <ul class="list-disc ml-5 space-y-1 mb-2">
                            <li><b>X25519</b> — key exchange &nbsp;·&nbsp; <b>Ed25519</b> — signatures and delivery proofs</li>
                            <li><b>AES-256 (CBC, PKCS7)</b> — payload encryption &nbsp;·&nbsp; <b>HMAC-SHA256</b> — integrity</li>
                            <li><b>HKDF</b> — key derivation &nbsp;·&nbsp; <b>SHA-256 / SHA-512</b> — hashing</li>
                        </ul>
                        <ul class="list-disc ml-5 space-y-1">
                            <li><b>End-to-end encryption.</b> Relays, gateways and propagation nodes cannot read what they carry.</li>
                            <li><b>Forward secrecy.</b> Links negotiate ephemeral session keys, so a key compromised later does not expose past traffic.</li>
                            <li><b>No metadata collection.</b> No sign-up, no contact upload, no central log.</li>
                            <li><b>Optional network isolation.</b> Interfaces can carry a name and passphrase; packets without the right code are dropped at the perimeter.</li>
                        </ul>
                        <p class="mt-2 border-l-4 border-amber-500 pl-3 text-gray-600 dark:text-gray-300">
                            Encryption protects content, not the existence of a transmission — a radio signal is
                            observable. An unlocked device or exported identity file is equivalent to holding the
                            address. Encrypted operation on business-band frequencies requires an FCC licence, and
                            rules vary by jurisdiction.
                        </p>
                    </section>

                    <!-- 10. checklist -->
                    <section>
                        <h3 class="font-bold text-base mb-2 text-blue-700 dark:text-blue-400">10. Requirements Checklist</h3>
                        <p class="mb-1"><b>Every device</b></p>
                        <ul class="list-disc ml-5 space-y-1 mb-2">
                            <li>An identity — generated at first launch, backed up somewhere safe</li>
                            <li>At least one interface — a radio, a Wi-Fi connection, or a TCP server address</li>
                            <li>An announce — sent once at setup, and again after any change in how you connect</li>
                        </ul>
                        <p class="mb-1"><b>Also worth knowing</b></p>
                        <ul class="list-disc ml-5 space-y-1">
                            <li>For offline delivery, at least one propagation node that stays powered.</li>
                            <li>For range, transport nodes with <code>enable_transport = Yes</code>, positioned high — and matching radio parameters on every device sharing a channel. A mismatch produces silence, not a slow link.</li>
                            <li>For live voice, a link with enough capacity: Wi-Fi, Ethernet, TCP, or LoRa at Short Fast or faster.</li>
                            <li>LoRa at 902–928 MHz is licence-free in the United States. Encrypted VHF/UHF business-band operation requires an FCC licence.</li>
                            <li><b>Not required:</b> accounts, subscriptions, SIM cards, phone numbers, DNS, DHCP, port forwarding, static IPs, or permission from any authority.</li>
                        </ul>
                    </section>

                    <div class="pt-3 border-t dark:border-zinc-700 space-y-2">
                        <a href="https://lcs.network/guide" target="_blank" class="inline-flex items-center gap-x-2 text-blue-600 dark:text-blue-400 underline font-medium">
                            Read the most recent guide at lcs.network/guide
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-4">
                                <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 6H5.25A2.25 2.25 0 0 0 3 8.25v10.5A2.25 2.25 0 0 0 5.25 21h10.5A2.25 2.25 0 0 0 18 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
                            </svg>
                        </a>
                        <div>
                            <a href="/manual/LCS_Network_Guide.pdf" target="_blank" class="text-blue-600 dark:text-blue-400 underline">
                                Open the full illustrated guide (PDF, includes network diagrams and use-case scenarios)
                            </a>
                        </div>
                        <div class="text-xs text-gray-500 dark:text-gray-400 pt-1">
                            Liberty Communication Systems, Inc. · lcs.network
                        </div>
                    </div>

                </div>
            </div>
        </div>

    </div>
</template>

<script>

export default {
    name: 'ToolsPage',
    data() {
        return {
            // LCS: About Reticulum guide dialog
            showGuide: false,
        };
    },
}
</script>
