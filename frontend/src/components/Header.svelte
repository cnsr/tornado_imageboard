<script>
    import { onMount } from "svelte";
    import { boards, loading } from "../stores/boards";
    import { Link } from "svelte-navigator";

    const url = "https://poorch.ga/api/boards";
    onMount(async () => {
        loading.set(true);
        fetch(url).then(response => response.json()).then(data => {
            console.log('received data', data);
            loading.set(false);
            $: boards.set(data);
        })
    })
</script>

<main class="main-container">
        <div class="boards-header">
            <Link to="/" class="board-link">[HOME]</Link>
            <Link to="/profile" class="board-link">[PROFILE]</Link>
            <Link to="/admin" class="board-link">[ADMIN]</Link>
            <span> </span>
            {#if !$loading}
                {#each $boards as board}
                    <a href={`/${board.short}`} class="board-link">[{board.short}]</a>
                {/each}
            {/if}
        </div>
    <div class="boards-header-right">
            <Link to="/" class="board-link">[MAP]</Link>
    </div>
</main>

<style>
    .main-container {
        display: flex;
        flex-direction: row;
    }
    .boards-header {
        display: flex;
        flex-direction: row;
        justify-content: start;
        width: 95%;
    }
    .boards-header-right {
        width: 5%;
    }
    :global(.boards-header *), :global(.board-link:visited) {
        color: navy;
        margin-right: .35rem !important;
    }
</style>