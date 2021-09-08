<script>
	import { Route, Router, Link } from 'svelte-navigator';
	import BoardSelector from "./components/BoardSelector.svelte";
	import Admin from "./components/Admin.svelte";
	import Board from "./components/Board.svelte";
	import Thread from "./components/Thread.svelte";
</script>

<Router>
	<header>

	</header>
	<main>
		<Route path="/">
			<BoardSelector />
		</Route>
		<Route path="admin">
			<Admin />
		</Route>
		<Route path="/:board">
			<Route path="/">
				<Board />
			</Route>
			<Route path=":id">
				<Thread />
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