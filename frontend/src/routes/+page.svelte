<script>
	import { onMount } from 'svelte';

	const API_URL = 'http://localhost:5001';

	let currentPage = $state('home');
	let showLogin = $state(false);
	let showReservation = $state(false);
	let isLoggedIn = $state(false);
	let loading = $state(false);

	let email = $state('');
	let password = $state('');
	let userId = $state(null);
	let userName = $state('');

	let selectedMachine = $state(null);
	let selectedDate = $state('');
	let selectedTime = $state('');

	let message = $state('');
	let machines = $state([]);
	let bookings = $state([]);

	onMount(async () => {
		await loadMachines();
	});

	function changePage(page) {
		currentPage = page;
		message = '';

		if (page === 'machines') {
			loadMachines();
		}

		if (page === 'bookings' && isLoggedIn) {
			loadBookings();
		}
	}

	function openLogin() {
		showLogin = true;
		message = '';
	}

	function closeLogin() {
		showLogin = false;
		password = '';
		message = '';
	}

	async function login() {
		if (!email || !password) {
			message = 'Please enter your email and password.';
			return;
		}

		loading = true;
		message = '';

		try {
			const response = await fetch(`${API_URL}/login`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					email: email,
					password: password
				})
			});

			const data = await response.json();

			if (!response.ok) {
				throw new Error(data.error || 'Login failed.');
			}

			userId = data.user_id;
			userName = data.name;
			isLoggedIn = true;
			showLogin = false;
			password = '';

			message = `Welcome, ${data.name}! You are logged in.`;

			await loadMachines();
			await loadBookings();
		} catch (error) {
			message = error.message;
		} finally {
			loading = false;
		}
	}

	function logout() {
		isLoggedIn = false;
		userId = null;
		userName = '';
		email = '';
		password = '';
		bookings = [];
		currentPage = 'home';
		message = 'You are logged out.';
	}

	async function loadMachines() {
		loading = true;

		try {
			const response = await fetch(
				`${API_URL}/machines?building_id=1`
			);

			const data = await response.json();

			if (!response.ok) {
				throw new Error(
					data.error || 'Could not load machines.'
				);
			}

			machines = data.map((machine) => ({
				id: machine.machine_id,

				name:
					machine.machine_type === 'washer'
						? `Washer ${machine.machine_number}`
						: `Dryer ${machine.machine_number}`,

				type:
					machine.machine_type === 'washer'
						? 'Washer'
						: 'Dryer',

				icon:
					machine.machine_type === 'washer'
						? '🧺'
						: '♨️',

				status:
					machine.status === 'available'
						? 'Available'
						: machine.status === 'in_use'
							? 'In Use'
							: machine.status === 'maintenance'
								? 'Maintenance'
								: 'Reserved',

				detail:
					machine.status === 'available'
						? `${machine.duration_minutes} minutes · $${Number(
								machine.cost_per_cycle
							).toFixed(2)}`
						: machine.status === 'in_use'
							? 'Currently in use'
							: machine.status === 'maintenance'
								? 'Under maintenance'
								: 'Currently reserved',

				duration: machine.duration_minutes,
				price: Number(machine.cost_per_cycle)
			}));
		} catch (error) {
			message = error.message;
		} finally {
			loading = false;
		}
	}

	async function loadBookings() {
		if (!userId) {
			return;
		}

		loading = true;

		try {
			const response = await fetch(
				`${API_URL}/users/${userId}/bookings`
			);

			const data = await response.json();

			if (!response.ok) {
				throw new Error(
					data.error || 'Could not load bookings.'
				);
			}

			bookings = data.map((booking) => ({
				id: booking.booking_id,
				machineId: booking.machine_id,

				machine:
					booking.machine_type === 'washer'
						? `Washer ${booking.machine_number}`
						: `Dryer ${booking.machine_number}`,

				type:
					booking.machine_type === 'washer'
						? 'Washer'
						: 'Dryer',

				date: formatDate(booking.start_time),
				time: formatTime(booking.start_time),
				endTime: formatTime(booking.end_time),

				price: Number(
					booking.price_at_booking
				).toFixed(2),

				status: formatStatus(
					booking.booking_status
				)
			}));
		} catch (error) {
			message = error.message;
		} finally {
			loading = false;
		}
	}

	function reserve(machine) {
		if (!isLoggedIn) {
			message =
				'Please log in before reserving a machine.';
			showLogin = true;
			return;
		}

		selectedMachine = machine;
		selectedDate = '';
		selectedTime = '';
		showReservation = true;
		message = '';
	}

	function closeReservation() {
		showReservation = false;
		selectedMachine = null;
		selectedDate = '';
		selectedTime = '';
		message = '';
	}

	async function confirmReservation() {
		if (!selectedDate || !selectedTime) {
			message = 'Please select a date and time.';
			return;
		}

		if (!userId || !selectedMachine) {
			message =
				'Please log in and choose a machine.';
			return;
		}

		loading = true;
		message = '';

		try {
			const startDate = createDateTime(
				selectedDate,
				selectedTime
			);

			const endDate = new Date(
				startDate.getTime() +
					selectedMachine.duration * 60 * 1000
			);

			const response = await fetch(
				`${API_URL}/bookings`,
				{
					method: 'POST',
					headers: {
						'Content-Type': 'application/json'
					},
					body: JSON.stringify({
						user_id: userId,
						machine_id: selectedMachine.id,
						start_time:
							formatForBackend(startDate),
						end_time:
							formatForBackend(endDate),
						price_at_booking:
							selectedMachine.price
					})
				}
			);

			const data = await response.json();

			if (!response.ok) {
				throw new Error(
					data.error ||
						'Could not create reservation.'
				);
			}

			showReservation = false;
			selectedMachine = null;
			selectedDate = '';
			selectedTime = '';
			currentPage = 'bookings';
			message =
				'Reservation created successfully.';

			await loadBookings();
			await loadMachines();
		} catch (error) {
			message = error.message;
		} finally {
			loading = false;
		}
	}

	async function cancelBooking(booking) {
		const confirmed = window.confirm(
			`Cancel the reservation for ${booking.machine}?`
		);

		if (!confirmed) {
			return;
		}

		loading = true;
		message = '';

		try {
			const response = await fetch(
				`${API_URL}/bookings/${booking.id}`,
				{
					method: 'DELETE'
				}
			);

			let data = {};

			try {
				data = await response.json();
			} catch {
				data = {};
			}

			if (!response.ok) {
				throw new Error(
					data.error ||
						'Could not cancel reservation.'
				);
			}

			message =
				'Reservation cancelled successfully.';

			await loadBookings();
			await loadMachines();
		} catch (error) {
			message = error.message;
		} finally {
			loading = false;
		}
	}

	function createDateTime(date, time) {
		const [timePart, period] = time.split(' ');
		let [hours, minutes] = timePart
			.split(':')
			.map(Number);

		if (period === 'PM' && hours !== 12) {
			hours += 12;
		}

		if (period === 'AM' && hours === 12) {
			hours = 0;
		}

		const result = new Date(`${date}T00:00:00`);
		result.setHours(hours, minutes, 0, 0);

		return result;
	}

	function formatForBackend(date) {
		const year = date.getFullYear();
		const month = String(
			date.getMonth() + 1
		).padStart(2, '0');
		const day = String(date.getDate()).padStart(
			2,
			'0'
		);
		const hours = String(date.getHours()).padStart(
			2,
			'0'
		);
		const minutes = String(
			date.getMinutes()
		).padStart(2, '0');
		const seconds = String(
			date.getSeconds()
		).padStart(2, '0');

		return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
	}

	function formatDate(value) {
		const date = new Date(value);

		return date.toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	}

	function formatTime(value) {
		const date = new Date(value);

		return date.toLocaleTimeString('en-US', {
			hour: 'numeric',
			minute: '2-digit'
		});
	}

	function formatStatus(status) {
		if (!status) {
			return 'Unknown';
		}

		return status
			.replaceAll('_', ' ')
			.replace(/\b\w/g, (letter) =>
				letter.toUpperCase()
			);
	}
</script>

<svelte:head>
	<title>WashWise</title>
	<meta
		name="description"
		content="Smart laundry machine reservations."
	/>
</svelte:head>

<header>
	<button
		class="logo"
		onclick={() => changePage('home')}
	>
		WashWise
	</button>

	<nav>
		<button onclick={() => changePage('home')}>
			Home
		</button>

		<button onclick={() => changePage('machines')}>
			Machines
		</button>

		<button onclick={() => changePage('bookings')}>
			My Bookings
		</button>

		{#if isLoggedIn}
			<span class="welcome">Hi, {userName}</span>

			<button class="login-button" onclick={logout}>
				Log Out
			</button>
		{:else}
			<button
				class="login-button"
				onclick={openLogin}
			>
				Log In
			</button>
		{/if}
	</nav>
</header>

<main>
	{#if message}
		<div class="message">{message}</div>
	{/if}

	{#if loading}
		<div class="loading">Loading...</div>
	{/if}

	{#if currentPage === 'home'}
		<section class="hero">
			<div class="hero-text">
				<p class="eyebrow">
					SMART LAUNDRY RESERVATIONS
				</p>

				<h1>
					Do your laundry without the waiting.
				</h1>

				<p class="description">
					Check real machine availability,
					reserve a time, and manage your laundry
					bookings from one simple dashboard.
				</p>

				<div class="buttons">
					<button
						class="primary"
						onclick={() =>
							changePage('machines')}
					>
						View Machines
					</button>

					<button
						class="secondary"
						onclick={() =>
							changePage('bookings')}
					>
						My Bookings
					</button>
				</div>
			</div>

			<div class="hero-card">
				<div class="bubble">🫧</div>

				<h2>Easy booking</h2>

				<p>
					Choose an available machine and
					reserve a convenient time.
				</p>

				<div class="stats">
					<div>
						<strong>{machines.length}</strong>
						<span>Machines</span>
					</div>

					<div>
						<strong>
							{machines.filter(
								(machine) =>
									machine.status ===
									'Available'
							).length}
						</strong>

						<span>Available</span>
					</div>
				</div>
			</div>
		</section>

		<section class="machine-section">
			<div class="section-header">
				<div>
					<p class="eyebrow">
						LIVE DATABASE AVAILABILITY
					</p>

					<h2>Available machines</h2>
				</div>

				<button
					class="refresh-button"
					onclick={loadMachines}
				>
					Refresh
				</button>
			</div>

			<div class="machine-grid">
				{#each machines as machine}
					<div class="machine-card">
						<div class="machine-top">
							<span class="icon">
								{machine.icon}
							</span>

							<span
								class:available={machine.status ===
									'Available'}
								class:unavailable={machine.status !==
									'Available'}
								class="status"
							>
								{machine.status}
							</span>
						</div>

						<h3>{machine.name}</h3>
						<p>{machine.type}</p>
						<strong>{machine.detail}</strong>

						<button
							class="reserve-button"
							disabled={machine.status !==
								'Available'}
							onclick={() =>
								reserve(machine)}
						>
							{machine.status ===
							'Available'
								? 'Reserve'
								: 'Unavailable'}
						</button>
					</div>
				{/each}
			</div>
		</section>
	{/if}

	{#if currentPage === 'machines'}
		<section class="page-section">
			<div class="section-header">
				<div>
					<p class="eyebrow">
						LIVE DATABASE AVAILABILITY
					</p>

					<h1>Available Machines</h1>
				</div>

				<button
					class="refresh-button"
					onclick={loadMachines}
				>
					Refresh
				</button>
			</div>

			{#if machines.length === 0 && !loading}
				<div class="empty">
					<h2>No machines found</h2>

					<p>
						The database did not return any
						machines for building 1.
					</p>
				</div>
			{:else}
				<div class="machine-grid">
					{#each machines as machine}
						<div class="machine-card">
							<div class="machine-top">
								<span class="icon">
									{machine.icon}
								</span>

								<span
									class:available={machine.status ===
										'Available'}
									class:unavailable={machine.status !==
										'Available'}
									class="status"
								>
									{machine.status}
								</span>
							</div>

							<h3>{machine.name}</h3>
							<p>{machine.type}</p>

							<strong>
								{machine.detail}
							</strong>

							<button
								class="reserve-button"
								disabled={machine.status !==
									'Available'}
								onclick={() =>
									reserve(machine)}
							>
								{machine.status ===
								'Available'
									? 'Reserve'
									: 'Unavailable'}
							</button>
						</div>
					{/each}
				</div>
			{/if}
		</section>
	{/if}

	{#if currentPage === 'bookings'}
		<section class="page-section">
			<div class="section-header">
				<div>
					<p class="eyebrow">
						DATABASE RESERVATIONS
					</p>

					<h1>My Bookings</h1>
				</div>

				{#if isLoggedIn}
					<button
						class="refresh-button"
						onclick={loadBookings}
					>
						Refresh
					</button>
				{/if}
			</div>

			{#if !isLoggedIn}
				<div class="empty">
					<div class="empty-icon">🔐</div>

					<h2>Please log in</h2>

					<p>
						Log in to view and manage your
						database reservations.
					</p>

					<button
						class="primary"
						onclick={openLogin}
					>
						Log In
					</button>
				</div>
			{:else if bookings.length === 0 && !loading}
				<div class="empty">
					<div class="empty-icon">🧺</div>

					<h2>No bookings found</h2>

					<p>
						Choose an available machine to
						create a reservation.
					</p>

					<button
						class="primary"
						onclick={() =>
							changePage('machines')}
					>
						View Machines
					</button>
				</div>
			{:else}
				<div class="booking-list">
					{#each bookings as booking}
						<div class="booking-card">
							<div>
								<span class="confirmed">
									{booking.status}
								</span>

								<h2>{booking.machine}</h2>
								<p>{booking.type}</p>
							</div>

							<div class="booking-detail">
								<span>Date</span>
								<strong>
									{booking.date}
								</strong>
							</div>

							<div class="booking-detail">
								<span>Time</span>
								<strong>
									{booking.time} –
									{booking.endTime}
								</strong>
							</div>

							<div class="booking-detail">
								<span>Price</span>
								<strong>
									${booking.price}
								</strong>
							</div>

							{#if booking.status !==
								'Cancelled' &&
							booking.status !== 'Completed'}
								<button
									class="cancel"
									onclick={() =>
										cancelBooking(
											booking
										)}
								>
									Cancel
								</button>
							{/if}
						</div>
					{/each}
				</div>
			{/if}
		</section>
	{/if}
</main>

{#if showLogin}
	<div class="modal-background">
		<div class="modal">
			<button class="close" onclick={closeLogin}>
				×
			</button>

			<p class="eyebrow">WELCOME BACK</p>
			<h2>Log in to WashWise</h2>

			<p class="modal-description">
				Use a real user account from the WashWise
				database.
			</p>

			<label for="email">Email</label>

			<input
				id="email"
				type="email"
				placeholder="adiallo@citymail.cuny.edu"
				bind:value={email}
			/>

			<label for="password">Password</label>

			<input
				id="password"
				type="password"
				placeholder="Enter password"
				bind:value={password}
			/>

			{#if message}
				<p class="error">{message}</p>
			{/if}

			<button
				class="primary full"
				onclick={login}
				disabled={loading}
			>
				{loading ? 'Logging in...' : 'Log In'}
			</button>
		</div>
	</div>
{/if}

{#if showReservation && selectedMachine}
	<div class="modal-background">
		<div class="modal">
			<button
				class="close"
				onclick={closeReservation}
			>
				×
			</button>

			<p class="eyebrow">NEW RESERVATION</p>

			<h2>Reserve {selectedMachine.name}</h2>

			<div class="machine-summary">
				<p>
					Duration:
					<strong>
						{selectedMachine.duration}
						minutes
					</strong>
				</p>

				<p>
					Price:
					<strong>
						${selectedMachine.price.toFixed(2)}
					</strong>
				</p>
			</div>

			<label for="date">Date</label>

			<input
				id="date"
				type="date"
				bind:value={selectedDate}
			/>

			<label for="time">Time</label>

			<select id="time" bind:value={selectedTime}>
				<option value="">Select a time</option>
				<option value="8:00 AM">8:00 AM</option>
				<option value="9:00 AM">9:00 AM</option>
				<option value="10:00 AM">10:00 AM</option>
				<option value="11:00 AM">11:00 AM</option>
				<option value="12:00 PM">12:00 PM</option>
				<option value="1:00 PM">1:00 PM</option>
				<option value="2:00 PM">2:00 PM</option>
				<option value="3:00 PM">3:00 PM</option>
				<option value="4:00 PM">4:00 PM</option>
				<option value="5:00 PM">5:00 PM</option>
				<option value="6:00 PM">6:00 PM</option>
				<option value="7:00 PM">7:00 PM</option>
			</select>

			{#if message}
				<p class="error">{message}</p>
			{/if}

			<button
				class="primary full"
				onclick={confirmReservation}
				disabled={loading}
			>
				{loading
					? 'Saving...'
					: 'Confirm Reservation'}
			</button>
		</div>
	</div>
{/if}

<style>
	:global(*) {
		box-sizing: border-box;
	}

	:global(body) {
		margin: 0;
		font-family:
			Arial, Helvetica, sans-serif;
		background: #f2f7fb;
		color: #173653;
	}

	button,
	input,
	select {
		font: inherit;
	}

	button {
		cursor: pointer;
	}

	button:disabled {
		cursor: not-allowed;
	}

	header {
		position: sticky;
		top: 0;
		z-index: 20;
		display: flex;
		align-items: center;
		justify-content: space-between;
		min-height: 86px;
		padding: 20px 7%;
		background: white;
		border-bottom: 1px solid #d7e4ed;
	}

	.logo {
		border: none;
		background: transparent;
		color: #087caf;
		font-size: 27px;
		font-weight: bold;
	}

	nav {
		display: flex;
		align-items: center;
		gap: 12px;
	}

	nav button {
		padding: 11px 14px;
		border: none;
		border-radius: 8px;
		background: transparent;
		color: #173653;
		font-weight: bold;
	}

	nav button:hover {
		background: #eaf5fa;
	}

	nav .login-button {
		padding: 12px 20px;
		background: #1682b3;
		color: white;
	}

	nav .login-button:hover {
		background: #096d99;
	}

	.welcome {
		color: #087caf;
		font-size: 14px;
		font-weight: bold;
	}

	main {
		min-height: calc(100vh - 86px);
	}

	.message,
	.loading {
		width: min(1100px, 88%);
		margin: 20px auto 0;
		padding: 14px 16px;
		border-radius: 10px;
		font-weight: bold;
	}

	.message {
		border: 1px solid #8ecde6;
		background: #e6f6fd;
		color: #08709d;
	}

	.loading {
		border: 1px solid #d8c47a;
		background: #fff9dc;
		color: #7c6500;
	}

	.hero {
		display: grid;
		grid-template-columns: 1.5fr 0.8fr;
		align-items: center;
		gap: 70px;
		width: min(1250px, 88%);
		margin: auto;
		padding: 80px 0;
	}

	.hero h1 {
		margin: 14px 0 24px;
		font-size: clamp(48px, 6vw, 68px);
		line-height: 1.05;
		letter-spacing: -2px;
	}

	.eyebrow {
		margin: 0;
		color: #0695a7;
		font-size: 14px;
		font-weight: bold;
		letter-spacing: 3px;
	}

	.description {
		max-width: 700px;
		color: #5c758b;
		font-size: 20px;
		line-height: 1.7;
	}

	.buttons {
		display: flex;
		gap: 14px;
		margin-top: 28px;
	}

	.primary,
	.secondary {
		padding: 14px 22px;
		border-radius: 10px;
		font-weight: bold;
	}

	.primary {
		border: none;
		background: #1682b3;
		color: white;
	}

	.primary:hover {
		background: #096d99;
	}

	.primary:disabled {
		background: #9cbac9;
	}

	.secondary {
		border: 1px solid #1682b3;
		background: white;
		color: #1682b3;
	}

	.hero-card {
		padding: 42px;
		border-radius: 30px;
		background: linear-gradient(
			135deg,
			#1682b3,
			#11aaa3
		);
		color: white;
		box-shadow: 0 18px 40px
			rgba(24, 102, 145, 0.18);
	}

	.hero-card h2 {
		font-size: 31px;
	}

	.bubble {
		font-size: 42px;
	}

	.stats {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 15px;
		margin-top: 25px;
	}

	.stats div {
		display: flex;
		flex-direction: column;
		padding: 20px;
		border-radius: 15px;
		background: rgba(255, 255, 255, 0.2);
	}

	.stats strong {
		font-size: 28px;
	}

	.machine-section,
	.page-section {
		width: min(1250px, 90%);
		margin: auto;
		padding: 50px 0 90px;
	}

	.machine-section h2,
	.page-section h1 {
		margin: 12px 0 30px;
		font-size: 38px;
	}

	.section-header {
		display: flex;
		align-items: flex-end;
		justify-content: space-between;
		gap: 20px;
		margin-bottom: 30px;
	}

	.refresh-button {
		padding: 11px 18px;
		border: 1px solid #aac8d9;
		border-radius: 9px;
		background: white;
		color: #294968;
		font-weight: bold;
	}

	.machine-grid {
		display: grid;
		grid-template-columns:
			repeat(4, minmax(0, 1fr));
		gap: 20px;
	}

	.machine-card {
		display: flex;
		flex-direction: column;
		min-height: 310px;
		padding: 26px;
		border: 1px solid #d4e2eb;
		border-radius: 20px;
		background: white;
		box-shadow: 0 8px 24px
			rgba(37, 76, 110, 0.06);
	}

	.machine-top {
		display: flex;
		align-items: center;
		justify-content: space-between;
	}

	.icon {
		font-size: 34px;
	}

	.status {
		padding: 7px 12px;
		border-radius: 20px;
		font-size: 13px;
		font-weight: bold;
	}

	.available {
		background: #d9f7e6;
		color: #12814e;
	}

	.unavailable {
		background: #fff0d7;
		color: #a86600;
	}

	.machine-card h3 {
		margin: 25px 0 8px;
		font-size: 23px;
	}

	.machine-card p {
		color: #738da2;
	}

	.reserve-button {
		width: 100%;
		margin-top: auto;
		padding: 13px;
		border: none;
		border-radius: 9px;
		background: #1682b3;
		color: white;
		font-weight: bold;
	}

	.reserve-button:hover {
		background: #096d99;
	}

	.reserve-button:disabled {
		background: #b8c7d1;
	}

	.empty {
		max-width: 650px;
		margin: 50px auto;
		padding: 55px;
		border: 1px solid #d4e2eb;
		border-radius: 20px;
		background: white;
		text-align: center;
	}

	.empty-icon {
		font-size: 50px;
	}

	.booking-list {
		display: grid;
		gap: 18px;
	}

	.booking-card {
		display: grid;
		grid-template-columns:
			1.5fr 1fr 1.4fr 0.7fr auto;
		align-items: center;
		gap: 20px;
		padding: 25px;
		border: 1px solid #d4e2eb;
		border-radius: 17px;
		background: white;
	}

	.booking-card h2 {
		margin: 12px 0 5px;
	}

	.booking-card p {
		margin: 0;
		color: #738da2;
	}

	.confirmed {
		padding: 6px 10px;
		border-radius: 20px;
		background: #d9f7e6;
		color: #12814e;
		font-size: 12px;
		font-weight: bold;
	}

	.booking-detail {
		display: flex;
		flex-direction: column;
		gap: 6px;
	}

	.booking-detail span {
		color: #738da2;
		font-size: 13px;
	}

	.cancel {
		padding: 11px 17px;
		border: 1px solid #c94b4b;
		border-radius: 9px;
		background: white;
		color: #b83d3d;
		font-weight: bold;
	}

	.cancel:hover {
		background: #fff0f0;
	}

	.modal-background {
		position: fixed;
		inset: 0;
		z-index: 100;
		display: grid;
		place-items: center;
		padding: 20px;
		background: rgba(9, 29, 46, 0.65);
	}

	.modal {
		position: relative;
		width: min(470px, 100%);
		padding: 38px;
		border-radius: 22px;
		background: white;
		box-shadow: 0 25px 70px
			rgba(0, 0, 0, 0.25);
	}

	.modal h2 {
		margin: 12px 0;
		font-size: 30px;
	}

	.modal-description {
		color: #6e879c;
		line-height: 1.5;
	}

	.close {
		position: absolute;
		top: 15px;
		right: 18px;
		border: none;
		background: transparent;
		color: #5d7487;
		font-size: 30px;
	}

	label {
		display: block;
		margin: 18px 0 8px;
		font-weight: bold;
	}

	input,
	select {
		width: 100%;
		padding: 13px;
		border: 1px solid #b7cbd8;
		border-radius: 9px;
		background: white;
		color: #173653;
	}

	input:focus,
	select:focus {
		outline: 2px solid #72c4e6;
		border-color: #1682b3;
	}

	.full {
		width: 100%;
		margin-top: 24px;
	}

	.error {
		color: #b53c3c;
		font-weight: bold;
	}

	.machine-summary {
		padding: 12px 16px;
		border-radius: 10px;
		background: #eef7fb;
	}

	.machine-summary p {
		margin: 7px 0;
	}

	@media (max-width: 1050px) {
		.hero {
			grid-template-columns: 1fr;
		}

		.machine-grid {
			grid-template-columns:
				repeat(2, minmax(0, 1fr));
		}

		.booking-card {
			grid-template-columns: 1fr 1fr;
		}
	}

	@media (max-width: 700px) {
		header {
			align-items: flex-start;
			flex-direction: column;
			gap: 15px;
		}

		nav {
			flex-wrap: wrap;
		}

		.hero {
			padding-top: 50px;
		}

		.hero h1 {
			font-size: 46px;
		}

		.machine-grid {
			grid-template-columns: 1fr;
		}

		.booking-card {
			grid-template-columns: 1fr;
		}

		.section-header {
			align-items: flex-start;
			flex-direction: column;
		}
	}
</style>