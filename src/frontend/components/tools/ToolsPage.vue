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
    </div>
</template>

<script>

export default {
    name: 'ToolsPage',
}
</script>
