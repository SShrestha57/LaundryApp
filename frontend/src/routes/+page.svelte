<script>
	let currentPage = $state('home');
	let showLogin = $state(false);
	let showReservation = $state(false);
	let isLoggedIn = $state(false);

	let email = $state('');
	let password = $state('');
	let selectedMachine = $state(null);
	let selectedDate = $state('');
	let selectedTime = $state('');
	let message = $state('');

	let machines = $state([
		{
			id: 1,
			name: 'Washer 1',
			type: 'Washer',
			icon: '🧺',
			status: 'Available',
			detail: 'Available now'
		},
		{
			id: 2,
			name: 'Washer 2',
			type: 'Washer',
			icon: '🧺',
			status: 'In Use',
			detail: '18 minutes left'
		},
		{
			id: 3,
			name: 'Dryer 1',
			type: 'Dryer',
			icon: '♨️',
			status: 'Available',
			detail: 'Available now'
		},
		{
			id: 4,
			name: 'Dryer 2',
			type: 'Dryer',
			icon: '♨️',
			status: 'Reserved',
			detail: 'Reserved until 2:30 PM'
		}
	]);

	let bookings = $state([]);

	function changePage(page) {
		currentPage = page;
		message = '';
	}

	function openLogin() {
		showLogin = true;
		message = '';
	}

	function closeLogin() {
		showLogin = false;
		message = '';
	}

	function login() {
		if (email === '' || password === '') {
			message = 'Please enter your email and password.';
			return;
		}

		isLoggedIn = true;
		showLogin = false;
		message = 'You are logged in successfully.';
	}

	function logout() {
		isLoggedIn = false;
		currentPage = 'home';
		message = 'You are logged out.';
	}

	function reserve(machine) {
		if (!isLoggedIn) {
			message = 'Please log in before reserving a machine.';
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
		message = '';
	}

	function confirmReservation() {
		if (selectedDate === '' || selectedTime === '') {
			message = 'Please select a date and time.';
			return;
		}

		bookings.push({
			id: Date.now(),
			machineId: selectedMachine.id,
			machine: selectedMachine.name,
			date: selectedDate,
			time: selectedTime
		});

		const machine = machines.find(
			(item) => item.id === selectedMachine.id
		);

		if (machine) {
			machine.status = 'Reserved';
			machine.detail = `Reserved for ${selectedTime}`;
		}

		showReservation = false;
		selectedMachine = null;
		currentPage = 'bookings';
		message = 'Reservation created successfully.';
	}

	function cancelBooking(booking) {
		const machine = machines.find(
			(item) => item.id === booking.machineId
		);

		if (machine) {
			machine.status = 'Available';
			machine.detail = 'Available now';
		}

		bookings = bookings.filter((item) => item.id !== booking.id);
		message = 'Reservation cancelled.';
	}
</script>

<svelte:head>
	<title>WashWise</title>
</svelte:head>

<header>
	<button class="logo" onclick={() => changePage('home')}>
		WashWise
	</button>

	<nav>
		<button onclick={() => changePage('home')}>Home</button>

		<button onclick={() => changePage('machines')}>
			Machines
		</button>

		<button onclick={() => changePage('bookings')}>
			My Bookings
		</button>

		{#if isLoggedIn}
			<button class="login-button" onclick={logout}>
				Log Out
			</button>
		{:else}
			<button class="login-button" onclick={openLogin}>
				Log In
			</button>
		{/if}
	</nav>
</header>

<main>
	{#if message}
		<div class="message">{message}</div>
	{/if}

	{#if currentPage === 'home'}
		<section class="hero">
			<div class="hero-text">
				<p class="eyebrow">SMART LAUNDRY RESERVATIONS</p>

				<h1>Do your laundry without the waiting.</h1>

				<p class="description">
					Check machine availability, reserve a time, and manage
					your laundry bookings from one simple dashboard.
				</p>

				<div class="buttons">
					<button
						class="primary"
						onclick={() => changePage('machines')}
					>
						View Machines
					</button>

					<button
						class="secondary"
						onclick={() => changePage('bookings')}
					>
						My Bookings
					</button>
				</div>
			</div>

			<div class="hero-card">
				<div class="bubble">🫧</div>

				<h2>Easy booking</h2>

				<p>
					Choose a machine and reserve the time that works best
					for you.
				</p>

				<div class="stats">
					<div>
						<strong>{machines.length}</strong>
						<span>Machines</span>
					</div>

					<div>
						<strong>
							{machines.filter(
								(machine) => machine.status === 'Available'
							).length}
						</strong>
						<span>Available</span>
					</div>
				</div>
			</div>
		</section>

		<section class="machine-section">
			<p class="eyebrow">LIVE AVAILABILITY</p>
			<h2>Available machines</h2>

			<div class="machine-grid">
				{#each machines as machine}
					<div class="machine-card">
						<div class="machine-top">
							<span class="icon">{machine.icon}</span>

							<span
								class:available={machine.status === 'Available'}
								class:unavailable={machine.status !== 'Available'}
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
							disabled={machine.status !== 'Available'}
							onclick={() => reserve(machine)}
						>
							{machine.status === 'Available'
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
			<p class="eyebrow">LIVE AVAILABILITY</p>
			<h1>Available Machines</h1>

			<div class="machine-grid">
				{#each machines as machine}
					<div class="machine-card">
						<div class="machine-top">
							<span class="icon">{machine.icon}</span>

							<span
								class:available={machine.status === 'Available'}
								class:unavailable={machine.status !== 'Available'}
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
							disabled={machine.status !== 'Available'}
							onclick={() => reserve(machine)}
						>
							{machine.status === 'Available'
								? 'Reserve'
								: 'Unavailable'}
						</button>
					</div>
				{/each}
			</div>
		</section>
	{/if}

	{#if currentPage === 'bookings'}
		<section class="page-section">
			<p class="eyebrow">YOUR RESERVATIONS</p>
			<h1>My Bookings</h1>

			{#if !isLoggedIn}
				<div class="empty">
					<h2>Please log in</h2>

					<p>
						Log in to view and manage your laundry bookings.
					</p>

					<button class="primary" onclick={openLogin}>
						Log In
					</button>
				</div>
			{:else if bookings.length === 0}
				<div class="empty">
					<h2>No bookings yet</h2>

					<p>
						Choose an available machine to make a reservation.
					</p>

					<button
						class="primary"
						onclick={() => changePage('machines')}
					>
						View Machines
					</button>
				</div>
			{:else}
				<div class="booking-list">
					{#each bookings as booking}
						<div class="booking-card">
							<div>
								<span class="confirmed">Confirmed</span>
								<h2>{booking.machine}</h2>
							</div>

							<div>
								<p>Date</p>
								<strong>{booking.date}</strong>
							</div>

							<div>
								<p>Time</p>
								<strong>{booking.time}</strong>
							</div>

							<button
								class="cancel"
								onclick={() => cancelBooking(booking)}
							>
								Cancel
							</button>
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
			<button class="close" onclick={closeLogin}>×</button>

			<p class="eyebrow">WELCOME BACK</p>
			<h2>Log in to WashWise</h2>

			<label for="email">Email</label>
			<input
				id="email"
				type="email"
				placeholder="student@example.com"
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

			<button class="primary full" onclick={login}>
				Log In
			</button>
		</div>
	</div>
{/if}

{#if showReservation && selectedMachine}
	<div class="modal-background">
		<div class="modal">
			<button class="close" onclick={closeReservation}>×</button>

			<p class="eyebrow">NEW RESERVATION</p>
			<h2>Reserve {selectedMachine.name}</h2>

			<label for="date">Date</label>
			<input
				id="date"
				type="date"
				bind:value={selectedDate}
			/>

			<label for="time">Time</label>
			<select id="time" bind:value={selectedTime}>
				<option value="">Select a time</option>
				<option value="9:00 AM">9:00 AM</option>
				<option value="10:00 AM">10:00 AM</option>
				<option value="11:00 AM">11:00 AM</option>
				<option value="12:00 PM">12:00 PM</option>
				<option value="1:00 PM">1:00 PM</option>
				<option value="2:00 PM">2:00 PM</option>
				<option value="3:00 PM">3:00 PM</option>
				<option value="4:00 PM">4:00 PM</option>
				<option value="5:00 PM">5:00 PM</option>
			</select>

			{#if message}
				<p class="error">{message}</p>
			{/if}

			<button class="primary full" onclick={confirmReservation}>
				Confirm Reservation
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
		font-family: Arial, sans-serif;
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

	header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 24px 7%;
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

	.login-button {
		background: #1682b3;
		color: white;
	}

	.message {
		width: min(1100px, 88%);
		margin: 20px auto;
		padding: 14px;
		border: 1px solid #8ecde6;
		border-radius: 10px;
		background: #e6f6fd;
		color: #08709d;
		font-weight: bold;
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
		font-size: 68px;
		line-height: 1.05;
	}

	.eyebrow {
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

	.secondary {
		border: 1px solid #1682b3;
		background: white;
		color: #1682b3;
	}

	.hero-card {
		padding: 42px;
		border-radius: 30px;
		background: linear-gradient(135deg, #1682b3, #11aaa3);
		color: white;
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

	.machine-grid {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
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

	.reserve-button:disabled {
		cursor: not-allowed;
		background: #b8c7d1;
	}

	.empty {
		max-width: 650px;
		margin: 50px auto;
		padding: 55px;
		border-radius: 20px;
		background: white;
		text-align: center;
	}

	.booking-list {
		display: grid;
		gap: 18px;
	}

	.booking-card {
		display: grid;
		grid-template-columns: 1.5fr 1fr 1fr auto;
		align-items: center;
		gap: 20px;
		padding: 25px;
		border-radius: 17px;
		background: white;
	}

	.confirmed {
		padding: 6px 10px;
		border-radius: 20px;
		background: #d9f7e6;
		color: #12814e;
		font-size: 12px;
		font-weight: bold;
	}

	.cancel {
		padding: 11px 17px;
		border: 1px solid #c94b4b;
		border-radius: 9px;
		background: white;
		color: #b83d3d;
		font-weight: bold;
	}

	.modal-background {
		position: fixed;
		inset: 0;
		display: grid;
		place-items: center;
		z-index: 100;
		padding: 20px;
		background: rgba(9, 29, 46, 0.65);
	}

	.modal {
		position: relative;
		width: min(470px, 100%);
		padding: 38px;
		border-radius: 22px;
		background: white;
	}

	.modal h2 {
		font-size: 30px;
	}

	.close {
		position: absolute;
		top: 15px;
		right: 18px;
		border: none;
		background: transparent;
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
	}

	.full {
		width: 100%;
		margin-top: 24px;
	}

	.error {
		color: #b53c3c;
		font-weight: bold;
	}

	@media (max-width: 950px) {
		.hero {
			grid-template-columns: 1fr;
		}

		.machine-grid {
			grid-template-columns: repeat(2, 1fr);
		}
	}

	@media (max-width: 650px) {
		header {
			align-items: flex-start;
			flex-direction: column;
			gap: 15px;
		}

		nav {
			flex-wrap: wrap;
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
	}
</style>