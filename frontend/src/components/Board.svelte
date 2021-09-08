<script>
    import fetchStore from '../stores/fetch';
    import { boards, currentBoard } from "../stores/boards";

    export let board;

    const url = "http://0.0.0.0:8000/api/boards";

    const [ data, loading, error, get ] = fetchStore(url);
    $: boards.set($data);
</script>

<main>
    {#if $loading}
        Loading...
    {:else if $error}
        Error: {$error}
    {:else}
        <div class="boards">
            {#each $boards as board}
                <div>
                    <div class="board-title">
                        <a href={`/${board.short}`}>/{board.short}/</a>
                        <p>{board.name}</p>
                    </div>
                    <div class="board-description">
                        {board.description}
                    </div>
                </div>
            {/each}
        </div>
    {/if}
</main>