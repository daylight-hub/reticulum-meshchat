<template>
    <div class="bg-white dark:bg-zinc-900 rounded shadow">

        <div class="flex border-b border-gray-300 dark:border-zinc-700 text-gray-700 dark:text-gray-200 p-2 font-semibold">Blackhole</div>

        <div class="divide-y divide-gray-300 dark:divide-zinc-700">

            <!-- what this is -->
            <div class="p-2 text-sm text-gray-600 dark:text-gray-400">
                Blocked identities are dropped at the transport layer: their announces are
                discarded and this node will not route traffic to any of their destinations.
                This applies to your own network segments only. Nothing here blocks anyone
                globally, and other nodes can still carry their traffic.
            </div>

            <!-- block by identity hash -->
            <div class="p-2">
                <label class="text-sm font-medium text-gray-900 dark:text-gray-100">Block an identity</label>
                <div class="mt-1 text-sm text-gray-600 dark:text-gray-400">
                    Paste an identity hash to block it directly. No announce or prior contact
                    is needed &mdash; Reticulum blocks identities, so knowing the hash is enough.
                    The <span class="font-mono">&lt;angle bracket&gt;</span> form RNS prints is
                    accepted, as is colon-delimited hex.
                </div>
                <div class="mt-2 flex gap-2">
                    <input v-model="newBlock" @keyup.enter="blockIdentity" type="text" placeholder="identity hash" class="grow bg-gray-50 dark:bg-zinc-700 border border-gray-300 dark:border-zinc-600 text-gray-900 dark:text-gray-100 text-sm rounded p-2 font-mono">
                    <input v-model="newBlockReason" type="text" placeholder="reason (optional)" class="w-48 bg-gray-50 dark:bg-zinc-700 border border-gray-300 dark:border-zinc-600 text-gray-900 dark:text-gray-100 text-sm rounded p-2">
                    <button @click="blockIdentity" type="button" class="shrink-0 bg-blue-500 hover:bg-blue-400 text-white rounded px-3 text-sm">Block</button>
                </div>
            </div>

            <!-- blocked list -->
            <div class="p-2">
                <div class="flex justify-between items-center">
                    <div class="text-sm font-medium text-gray-900 dark:text-gray-100">
                        Blocked Identities ({{ blackholed.length }})
                    </div>
                    <button @click="load" type="button" class="text-sm text-blue-500 hover:underline">Refresh</button>
                </div>

                <div v-if="blackholed.length === 0" class="mt-2 text-sm text-gray-500 dark:text-gray-400">
                    Nothing is blocked. Use Block Contact in a conversation's menu to add someone.
                </div>

                <div v-else class="mt-2 divide-y divide-gray-200 dark:divide-zinc-700">
                    <div v-for="entry of blackholed" :key="entry.identity_hash" class="flex items-center gap-2 py-1.5">
                        <div class="grow min-w-0">
                            <div class="font-mono text-sm text-gray-900 dark:text-gray-100 truncate">{{ entry.identity_hash }}</div>
                            <div class="text-xs text-gray-500 dark:text-gray-400">
                                <span v-if="entry.local">Added by you</span>
                                <span v-else>From source {{ entry.source ?? 'unknown' }}</span>
                                <span v-if="entry.until"> &middot; until {{ formatUntil(entry.until) }}</span>
                                <span v-else> &middot; indefinitely</span>
                                <span v-if="entry.reason"> &middot; {{ entry.reason }}</span>
                            </div>
                        </div>
                        <button @click="unblock(entry)" type="button" class="shrink-0 text-sm text-blue-500 hover:underline">Unblock</button>
                    </div>
                </div>
            </div>

            <!-- publish -->
            <div class="p-2">
                <div class="flex items-center">
                    <input v-model="config.publish_blackhole" @change="save" type="checkbox" class="w-4 h-4 border border-gray-300 dark:border-zinc-600 rounded bg-gray-50 dark:bg-zinc-700 focus:ring-3 focus:ring-blue-300 dark:focus:ring-blue-600">
                    <label class="ml-2 text-sm font-medium text-gray-900 dark:text-gray-100">Publish my blocked list</label>
                </div>
                <div class="mt-1 text-sm text-gray-600 dark:text-gray-400">
                    Lets other nodes subscribe to your list. They fetch it from
                    <span class="font-mono">rnstransport.info.blackhole</span>.
                    <span v-if="config.identity_hash">
                        Your <em>transport instance</em> identity is
                        <span class="font-mono break-all">{{ config.identity_hash }}</span> &mdash;
                        that is what subscribers add as a source. It is not your
                        MeshChat identity, which is a different key.
                    </span>
                </div>
            </div>

            <!-- subscribe -->
            <div class="p-2">
                <label class="text-sm font-medium text-gray-900 dark:text-gray-100">Subscribe to lists</label>
                <div class="mt-1 text-sm text-amber-600 dark:text-amber-500">
                    A source you subscribe to decides who you can reach. Only add maintainers
                    you trust, and check what a list contains before adding it.
                </div>

                <div class="mt-2 space-y-1">
                    <div v-for="(source, index) of config.blackhole_sources" :key="index" class="flex items-center gap-2">
                        <div class="grow font-mono text-sm text-gray-900 dark:text-gray-100 truncate">{{ source }}</div>
                        <button @click="removeSource(index)" type="button" class="shrink-0 text-sm text-blue-500 hover:underline">Remove</button>
                    </div>
                </div>

                <div class="mt-2 flex gap-2">
                    <input v-model="newSource" type="text" placeholder="transport identity hash" class="grow bg-gray-50 dark:bg-zinc-700 border border-gray-300 dark:border-zinc-600 text-gray-900 dark:text-gray-100 text-sm rounded p-2 font-mono">
                    <button @click="addSource" type="button" class="shrink-0 bg-blue-500 hover:bg-blue-400 text-white rounded px-3 text-sm">Add</button>
                </div>

                <div class="mt-2 flex items-center gap-2">
                    <label class="text-sm text-gray-900 dark:text-gray-100">Update every</label>
                    <input v-model.number="config.blackhole_update_interval" @change="save" type="number" min="1" class="w-24 bg-gray-50 dark:bg-zinc-700 border border-gray-300 dark:border-zinc-600 text-gray-900 dark:text-gray-100 text-sm rounded p-1">
                    <span class="text-sm text-gray-900 dark:text-gray-100">minutes</span>
                </div>
            </div>

            <!-- restart notice -->
            <div v-if="requiresRestart" class="p-2 text-sm text-amber-600 dark:text-amber-500">
                Reticulum reads publish and subscribe settings when it starts, so restart
                MeshChat to apply them. Blocking and unblocking take effect immediately.
            </div>

        </div>
    </div>
</template>

<script>
import DialogUtils from "../../js/DialogUtils";

export default {
    name: 'BlackholeSettings',
    data() {
        return {
            blackholed: [],
            config: {
                publish_blackhole: false,
                blackhole_sources: [],
                blackhole_update_interval: 60,
                identity_hash: null,
            },
            newSource: "",
            newBlock: "",
            newBlockReason: "",
            requiresRestart: false,
        };
    },
    mounted() {
        this.load();
    },
    methods: {
        async load() {
            try {
                const response = await window.axios.get("/api/v1/blackhole");
                this.blackholed = response.data.blackholed;
                this.config = response.data.config;
            } catch(e) {
                // leave defaults in place, the section stays usable
            }
        },
        async save() {
            try {
                const response = await window.axios.patch("/api/v1/blackhole/config", {
                    publish_blackhole: this.config.publish_blackhole,
                    blackhole_sources: this.config.blackhole_sources,
                    blackhole_update_interval: this.config.blackhole_update_interval,
                });
                this.config = response.data.config;
                this.requiresRestart = true;
            } catch(e) {
                DialogUtils.alert(e.response?.data?.message ?? "Failed to save blackhole settings.");
                await this.load();
            }
        },
        async blockIdentity() {

            const identityHash = this.newBlock.trim().toLowerCase();
            if(identityHash === ""){
                return;
            }

            try {
                await window.axios.post("/api/v1/blackhole", {
                    identity_hash: identityHash,
                    reason: this.newBlockReason.trim() !== "" ? this.newBlockReason.trim() : null,
                });
                this.newBlock = "";
                this.newBlockReason = "";
                await this.load();
            } catch(e) {
                DialogUtils.alert(e.response?.data?.message ?? "Failed to block identity.");
            }

        },
        async addSource() {
            const source = this.newSource.trim().toLowerCase();
            if(source === ""){
                return;
            }
            if(this.config.blackhole_sources.includes(source)){
                this.newSource = "";
                return;
            }
            this.config.blackhole_sources.push(source);
            this.newSource = "";
            await this.save();
        },
        async removeSource(index) {
            this.config.blackhole_sources.splice(index, 1);
            await this.save();
        },
        async unblock(entry) {
            if(!await DialogUtils.confirm(`Unblock ${entry.identity_hash}?`)){
                return;
            }
            try {
                await window.axios.delete(`/api/v1/blackhole/${entry.identity_hash}`);
                await this.load();
            } catch(e) {
                DialogUtils.alert(e.response?.data?.message ?? "Failed to unblock identity.");
            }
        },
        formatUntil(until) {
            return new Date(until * 1000).toLocaleString();
        },
    },
}
</script>
