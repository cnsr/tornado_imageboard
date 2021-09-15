<script>
    import { boards, currentBoard, loading, threads } from "../stores/boards";
    import {onMount} from "svelte";

    export let board;

    console.log('board is ', board);

    const url = `https://poorch.ga/api/board/${board}`;
    onMount(async () => {
        loading.set(true);
        fetch(url).then(response => response.json()).then(data => {
            console.log('received data 2', data);
            loading.set(false);
            $: threads.set(data);
        })
    })


</script>

<main>
    {#if $loading}
        Loading...
    {:else}
        <div class="boards">
            {#each $threads as thread}
                {thread}
            {/each}
        </div>
    {/if}
</main>