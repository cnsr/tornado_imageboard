<script>
	import { Route, Router, Link } from 'svelte-navigator';
	import BoardSelector from "./components/BoardSelector.svelte";
	import Admin from "./components/Admin.svelte";
	import Board from "./components/Board.svelte";
	import Thread from "./components/Thread.svelte";
	import Header from "./components/Header.svelte";
</script>

<Router>
	<header>
		<Header />
	</header>
	<main>
		<Route path="/">
			<BoardSelector />
		</Route>
		<Route path="admin">
			<Admin />
		</Route>
		<Route path="/:board" let:params>
			<Route path="/">
				<Board board={params.board}/>
			</Route>
			<Route path="/:threadId">
				<Thread board={params.board}/>
			</Route>
		</Route>
	</main>
</Router>

<style>
	main {
		text-align: center;
		padding: 1em;
		max-width: 240px;
		margin: 0 auto;
	}
	@media (min-width: 640px) {
		main {
			max-width: none;
		}
	}
</style>