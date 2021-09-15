<script>
    import { replaceText } from '../utils/text';

    export let post;
    let isThread = post.thread === null;
    // process post
    post.text = replaceText(post.text);

    // console.log(post);
</script>

<main>
    <div id={`post-${post.id}`} class='post'>
        <div class="post-header">{post.subject || ''}</div>
        <div class="post-body">{@html post.text}</div>
        {#if isThread}
            is a thread
        {/if}
    </div>
</main>

<style>
    .post {
        border: 1px solid black;
        display: flex;
        flex-direction: column;
        align-items: start;
        padding: 2px 4px;
        margin-bottom: .5rem;
    }
</style>