<script>
    import fetchStore from '../stores/fetch';
    import {boards} from "../stores/boards";

    export let board;

    $: boards.set($data);
</script>

<main>
    {#if $boards}
        <div className="boards">
            {#each $boards as board}
                <div>
                    <div className="board-title">
                        <a href={`/${board.short}`}>/{board.short}/</a>
                        <p>{board.name}</p>
                    </div>
                    <div className="board-description">
                        {board.description}
                    </div>
                </div>
            {/each}
        </div>
    {:else}
        Failed to load boards.
    {/if}
</main>