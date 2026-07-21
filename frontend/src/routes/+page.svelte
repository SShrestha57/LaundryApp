<script>
	import { fade, fly, scale } from 'svelte/transition';
	import { onMount } from 'svelte';

	const API_URL = 'http://127.0.0.1:5001';
	const buildings = ['Maple Court', 'Harbor House', 'The Linden', 'Parkside Lofts'];

	let currentPage = $state('home');
	let showAuth = $state(false);
	let authMode = $state('signin');
	let authAudience = $state('resident');
	let showReservation = $state(false);
	let isLoggedIn = $state(false);
	let loading = $state(false);
	let message = $state('');
	let email = $state('');
	let password = $state('');
	let userId = $state(null);
	let userName = $state('');
	let userRole = $state('');
	let userBuildingId = $state(1);
	let signup = $state({ name: '', email: '', phone: '', card: '', building: '' });
	let pricingAudience = $state('landlord');
	let selectedMachine = $state(null);
	let selectedDate = $state('');
	let selectedTime = $state('');
	let machines = $state([]);
	let bookings = $state([]);
	let managerRevenue = $state(null);
	let managerSubscription = $state(null);

	onMount(loadMachines);

	function changePage(page) {
		currentPage = page;
		message = '';
		if (page === 'machines') loadMachines();
		if (page === 'bookings' && isLoggedIn) loadBookings();
		if (page === 'dashboard' && userRole === 'manager') loadDashboard();
		window.scrollTo({ top: 0, behavior: 'smooth' });
	}

	function openAuth(mode = 'signin', audience = 'resident') {
		authMode = mode;
		authAudience = audience;
		message = '';
		showAuth = true;
	}

	function closeAuth() {
		showAuth = false;
		password = '';
		message = '';
	}

	async function login() {
		if (!email || !password) return (message = 'Enter your email and password to continue.');
		loading = true;
		message = '';
		try {
			const response = await fetch(`${API_URL}/login`, {
				method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email, password })
			});
			const data = await response.json();
			if (!response.ok) throw new Error(data.error || 'We could not sign you in.');
			userId = data.user_id;
			userName = data.name;
			userRole = data.role;
			userBuildingId = data.building_id;
			isLoggedIn = true;
			showAuth = false;
			password = '';
			await loadMachines();
			if (userRole === 'manager') { await loadDashboard(); changePage('dashboard'); }
			else { await loadBookings(); changePage('machines'); }
			message = `Welcome back, ${data.name}.`;
		} catch (error) { message = error.message; }
		finally { loading = false; }
	}

	function createAccount() {
		if (!signup.name || !signup.email || !signup.phone || !signup.building) {
			message = 'Please complete your contact details and select your building.';
			return;
		}
		message = `Thanks, ${signup.name.split(' ')[0]}! Your resident account request for ${signup.building} is ready for setup.`;
		authMode = 'signin';
		email = signup.email;
		password = '';
	}

	function logout() {
		isLoggedIn = false; userId = null; userName = ''; userRole = ''; userBuildingId = 1; email = ''; password = ''; bookings = [];
		changePage('home'); message = 'You have been signed out.';
	}

	async function loadMachines() {
		loading = true;
		try {
			const response = await fetch(`${API_URL}/machines?building_id=${userBuildingId}`);
			const data = await response.json();
			if (!response.ok) throw new Error(data.error || 'Could not load machines.');
			machines = data.map((machine) => ({
				id: machine.machine_id,
				name: `${machine.machine_type === 'washer' ? 'Washer' : 'Dryer'} ${machine.machine_number}`,
				type: machine.machine_type === 'washer' ? 'Washer' : 'Dryer',
				icon: machine.machine_type === 'washer' ? '◉' : '◌',
				status: machine.status === 'active' ? 'Available' : machine.status === 'in_use' ? 'In use' : machine.status === 'maintenance' ? 'Maintenance' : 'Reserved',
				detail: machine.status === 'active' ? `${machine.duration_minutes} min cycle · $${Number(machine.cost_per_cycle).toFixed(2)}` : machine.status === 'in_use' ? 'Currently running' : machine.status === 'maintenance' ? 'Temporarily offline' : 'Held for a resident',
				duration: machine.duration_minutes, price: Number(machine.cost_per_cycle)
			}));
		} catch (error) { message = error.message; }
		finally { loading = false; }
	}

	async function loadBookings() {
		if (!userId) return;
		loading = true;
		try {
			const response = await fetch(`${API_URL}/users/${userId}/bookings`);
			const data = await response.json();
			if (!response.ok) throw new Error(data.error || 'Could not load your bookings.');
			bookings = data.map((booking) => ({
				id: booking.booking_id, machine: `${booking.machine_type === 'washer' ? 'Washer' : 'Dryer'} ${booking.machine_number}`,
				date: formatDate(booking.start_time), time: formatTime(booking.start_time), endTime: formatTime(booking.end_time),
				price: Number(booking.price_at_booking).toFixed(2), status: formatStatus(booking.booking_status)
			}));
		} catch (error) { message = error.message; }
		finally { loading = false; }
	}

	async function loadDashboard() {
		await Promise.all([loadMachines(), loadManagerRevenue(), loadManagerSubscription()]);
	}

	async function loadManagerRevenue() {
		try {
			const response = await fetch(`${API_URL}/reports/revenue`); const data = await response.json();
			if (!response.ok) throw new Error(data.error || 'Could not load revenue.');
			managerRevenue = data.find((row) => Number(row.building_id) === userBuildingId) || { booking_revenue: 0, subscription_revenue: 0 };
		} catch (error) { managerRevenue = null; }
	}

	async function loadManagerSubscription() {
		try {
			const response = await fetch(`${API_URL}/subscriptions`); const data = await response.json();
			if (!response.ok) throw new Error(data.error || 'Could not load subscription.');
			managerSubscription = data.find((row) => Number(row.building_id) === userBuildingId) || null;
		} catch (error) { managerSubscription = null; }
	}

	function exportRevenue() {
		const link = document.createElement('a');
		link.href = `${API_URL}/reports/revenue/export`;
		link.download = 'revenue_report.xlsx';
		document.body.appendChild(link);
		link.click();
		link.remove();
	}

	function reserve(machine) {
		if (!isLoggedIn) { message = 'Sign in as a resident to reserve a machine.'; openAuth('signin', 'resident'); return; }
		if (userRole === 'manager') { message = 'Manager accounts can view machine status but cannot make resident reservations.'; return; }
		selectedMachine = machine; selectedDate = ''; selectedTime = ''; showReservation = true; message = '';
	}

	function closeReservation() { showReservation = false; selectedMachine = null; selectedDate = ''; selectedTime = ''; message = ''; }

	async function confirmReservation() {
		if (!selectedDate || !selectedTime) return (message = 'Choose a date and a time first.');
		loading = true;
		try {
			const startDate = createDateTime(selectedDate, selectedTime);
			const endDate = new Date(startDate.getTime() + selectedMachine.duration * 60000);
			const response = await fetch(`${API_URL}/bookings`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ user_id: userId, machine_id: selectedMachine.id, start_time: formatForBackend(startDate), end_time: formatForBackend(endDate), price_at_booking: selectedMachine.price }) });
			const data = await response.json();
			if (!response.ok) throw new Error(data.error || 'Could not confirm the reservation.');
			closeReservation(); await loadBookings(); await loadMachines(); changePage('bookings'); message = 'Your laundry time is confirmed.';
		} catch (error) { message = error.message; }
		finally { loading = false; }
	}

	async function cancelBooking(booking) {
		if (!window.confirm(`Cancel ${booking.machine} on ${booking.date}?`)) return;
		loading = true;
		try { const response = await fetch(`${API_URL}/bookings/${booking.id}`, { method: 'DELETE' }); if (!response.ok) throw new Error('Could not cancel this booking.'); await loadBookings(); await loadMachines(); message = 'Reservation cancelled.'; }
		catch (error) { message = error.message; } finally { loading = false; }
	}

	function createDateTime(date, time) { const [part, period] = time.split(' '); let [hours, minutes] = part.split(':').map(Number); if (period === 'PM' && hours !== 12) hours += 12; if (period === 'AM' && hours === 12) hours = 0; const result = new Date(`${date}T00:00:00`); result.setHours(hours, minutes, 0, 0); return result; }
	function formatForBackend(date) { return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}:00`; }
	function formatDate(value) { return new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }); }
	function formatTime(value) { return new Date(value).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' }); }
	function formatStatus(status) { return (status || 'confirmed').replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase()); }
</script>

<svelte:head><title>Rinse — laundry, on your time</title><meta name="description" content="A better laundry experience for apartment communities." /></svelte:head>

<header>
	<button class="brand" onclick={() => changePage('home')} aria-label="Rinse home"><span class="brand-mark">r</span> rinse</button>
	<nav aria-label="Main navigation">
		<button class:active={currentPage === 'machines'} onclick={() => changePage('machines')}>Find a machine</button>
		<button class:active={currentPage === 'pricing'} onclick={() => changePage('pricing')}>For properties</button>
		{#if isLoggedIn && userRole === 'manager'}<button class:active={currentPage === 'dashboard'} onclick={() => changePage('dashboard')}>Dashboard</button>{/if}
		{#if isLoggedIn && userRole !== 'manager'}<button class:active={currentPage === 'bookings'} onclick={() => changePage('bookings')}>My laundry</button>{/if}
	</nav>
	<div class="header-actions">
		{#if isLoggedIn}<span class="user-name">{userName}</span><button class="text-button" onclick={logout}>Sign out</button>
		{:else}<button class="text-button" onclick={() => openAuth('signin', 'resident')}>Sign in</button><button class="button small" onclick={() => openAuth('signup', 'resident')}>Get started</button>{/if}
	</div>
</header>

{#if message}<div class="notice" transition:fly={{ y: -10, duration: 220 }}><span>✦</span>{message}<button onclick={() => (message = '')} aria-label="Dismiss">×</button></div>{/if}

<main>
	{#if currentPage === 'home'}
		<div class="page" in:fade={{ duration: 260 }}>
			<section class="hero wrap">
				<div class="hero-copy">
					<p class="kicker">Laundry, without the waiting</p>
					<h1>One less thing<br />to plan around.</h1>
					<p class="lead">See what’s open, book a time that works, and pay before you head downstairs.</p>
					<div class="hero-actions"><button class="button" onclick={() => changePage('machines')}>Check availability <span>→</span></button><button class="link-button" onclick={() => openAuth('signup', 'resident')}>Create resident account</button></div>
					<div class="trust-line"><span>●</span> Live availability from your building</div>
				</div>
				<div class="hero-visual" aria-label="Laundry booking preview">
					<div class="glow"></div><div class="visual-top"><span>Good afternoon, Maya</span><span class="avatar">M</span></div>
					<div class="visual-title">Your next wash</div><div class="reservation-preview"><div class="machine-dot washer">◉</div><div><strong>Washer 04</strong><span>Today · 6:30–7:05 PM</span></div><b>$2.50</b></div>
					<div class="availability-row"><span>Available now</span><b>{machines.filter((machine) => machine.status === 'Available').length} machines</b></div>
					<div class="mini-machines">{#each machines.slice(0, 4) as machine}<div class:open={machine.status === 'Available'}><i>{machine.icon}</i><span>{machine.name.slice(-2)}</span></div>{/each}</div>
				</div>
			</section>
			<section class="benefits wrap"><div><p class="kicker">A calmer laundry room</p><h2>Built around real life.</h2></div><div class="benefit-list"><article><span>01</span><h3>Know before you go</h3><p>Real-time availability keeps the guessing out of laundry day.</p></article><article><span>02</span><h3>Reserve your window</h3><p>Choose a machine and a time, then get on with your day.</p></article><article><span>03</span><h3>Simple at checkout</h3><p>Pay securely when you book—no coins, no scrambling.</p></article></div></section>
			<section class="property-banner wrap"><div><p class="kicker">For property teams</p><h2>Better operations start<br />with better visibility.</h2></div><div><p>Give residents a thoughtful amenity while your team manages machines, pricing, and performance in one place.</p><button class="button light" onclick={() => changePage('pricing')}>Explore Rinse for properties <span>→</span></button></div></section>
		</div>
	{:else if currentPage === 'machines'}
		<section class="page wrap" in:fade={{ duration: 220 }}><div class="section-intro"><p class="kicker">{isLoggedIn ? 'Your building · Maple Court' : 'Maple Court · Live status'}</p><h1>Find your next machine.</h1><p>Availability updates as cycles start and end.</p></div><div class="toolbar"><div class="filter-pills"><button class="selected">All machines</button><button>Washers</button><button>Dryers</button></div><button class="icon-button" onclick={loadMachines} aria-label="Refresh availability">↻ Refresh</button></div><div class="machine-grid">{#each machines as machine}<article class="machine-card" transition:scale={{ duration: 180, start: 0.96 }}><div class="machine-card-top"><span class="machine-symbol {machine.type.toLowerCase()}">{machine.icon}</span><span class:available={machine.status === 'Available'} class="status">{machine.status}</span></div><h3>{machine.name}</h3><p>{machine.type} · {machine.detail}</p><button class="card-action" disabled={machine.status !== 'Available'} onclick={() => reserve(machine)}>{machine.status === 'Available' ? 'Reserve this machine' : 'Not available'} <span>→</span></button></article>{/each}</div></section>
	{:else if currentPage === 'bookings'}
		<section class="page wrap" in:fade={{ duration: 220 }}><div class="section-intro"><p class="kicker">Resident account</p><h1>Your laundry schedule.</h1><p>Everything you have booked, all in one place.</p></div>{#if !isLoggedIn}<div class="empty-state"><div class="empty-icon">◉</div><h2>Your next wash is waiting.</h2><p>Sign in to view, manage, and reserve your building’s machines.</p><button class="button" onclick={() => openAuth('signin', 'resident')}>Sign in as resident</button></div>{:else if bookings.length === 0 && !loading}<div class="empty-state"><div class="empty-icon">◎</div><h2>Nothing booked yet.</h2><p>Choose an available machine and make the time yours.</p><button class="button" onclick={() => changePage('machines')}>Find a machine</button></div>{:else}<div class="booking-list">{#each bookings as booking}<article class="booking-card" transition:fly={{ y: 12, duration: 180 }}><div class="booking-main"><span class="confirmed">{booking.status}</span><h2>{booking.machine}</h2><p>{booking.date} · {booking.time}–{booking.endTime}</p></div><div class="booking-price"><span>Paid</span><b>${booking.price}</b></div>{#if booking.status !== 'Cancelled' && booking.status !== 'Completed'}<button class="cancel-button" onclick={() => cancelBooking(booking)}>Cancel</button>{/if}</article>{/each}</div>{/if}</section>
	{:else if currentPage === 'pricing'}
		<section class="page pricing-page" in:fade={{ duration: 220 }}><div class="wrap"><div class="section-intro centered"><p class="kicker">One service, two experiences</p><h1>Built for better laundry days.</h1><p>Rinse gives property teams control behind the scenes and residents an easy way to get laundry done.</p></div><div class="audience-toggle"><button class:chosen={pricingAudience === 'landlord'} onclick={() => (pricingAudience = 'landlord')}>For properties</button><button class:chosen={pricingAudience === 'resident'} onclick={() => (pricingAudience = 'resident')}>For residents</button></div>{#if pricingAudience === 'landlord'}<div class="pricing-grid"><article class="price-card"><p class="plan-label">Starter</p><h2>Small buildings,<br />big relief.</h2><div class="price"><b>$79</b><span>/ month</span></div><p class="price-copy">For properties with up to 25 machines.</p><ul><li>Resident booking portal</li><li>Machine status overview</li><li>Flexible per-machine pricing</li><li>Monthly revenue summary</li></ul><button class="button full-width" onclick={() => openAuth('signin', 'manager')}>Property team sign in</button></article><article class="price-card featured"><span class="popular">Most popular</span><p class="plan-label">Growth</p><h2>Made for a<br />fuller building.</h2><div class="price"><b>$149</b><span>/ month</span></div><p class="price-copy">For communities with up to 75 machines.</p><ul><li>Everything in Starter</li><li>Performance analytics</li><li>Automated resident reminders</li><li>Priority support</li></ul><button class="button full-width" onclick={() => openAuth('signin', 'manager')}>Talk to us <span>→</span></button></article><article class="price-card"><p class="plan-label">Portfolio</p><h2>For every<br />building you run.</h2><div class="price"><b>Let’s talk</b></div><p class="price-copy">Custom rollout for multi-property teams.</p><ul><li>Everything in Growth</li><li>Multi-building management</li><li>Custom reporting</li><li>Dedicated onboarding</li></ul><button class="outline-button full-width" onclick={() => openAuth('signin', 'manager')}>Contact sales</button></article></div><p class="pricing-note">All plans include secure resident payments. Machine cycle prices are set by your property team.</p>{:else}<div class="resident-price"><div><p class="plan-label">For residents</p><h2>Your building sets the price. We make it simple.</h2><p>There’s no Rinse subscription for residents. Create a free account, select your building, and pay only for the washer or dryer cycle you reserve.</p><button class="button" onclick={() => openAuth('signup', 'resident')}>Create free account <span>→</span></button></div><div class="resident-receipt"><p>Example booking</p><div><span>Washer 04 · 35 min</span><b>$2.50</b></div><div><span>Service fee</span><b>$0.00</b></div><hr /><div class="total"><span>Total today</span><b>$2.50</b></div><small>Cycle prices vary by building and are set by its property team.</small></div></div>{/if}</div></section>
	{:else if currentPage === 'dashboard'}
		<section class="page wrap dashboard" in:fade={{ duration: 220 }}>{#if !isLoggedIn || userRole !== 'manager'}<div class="empty-state"><div class="empty-icon">▦</div><h2>Property team access only.</h2><p>Sign in with your developer or admin account to manage your building.</p><button class="button" onclick={() => openAuth('signin', 'manager')}>Property team sign in</button></div>{:else}<div class="dashboard-heading"><div><p class="kicker">{managerRevenue?.building || 'Property'} · Property workspace</p><h1>Good morning, {userName}.</h1><p>Here’s what is happening in your laundry room today.</p></div><button class="icon-button" onclick={loadDashboard}>↻ Refresh data</button></div><div class="metric-grid"><article><span>Available now</span><b>{machines.filter((machine) => machine.status === 'Available').length}<small> / {machines.length} machines</small></b><p class="positive">● Healthy availability</p></article><article><span>Maintenance</span><b>{machines.filter((machine) => machine.status === 'Maintenance').length}</b><p>Machines requiring attention</p></article><article><span>Booking fees</span><b>${Number(managerRevenue?.booking_revenue || 0).toFixed(2)}</b><p>Platform revenue to date</p></article><article><span>Current plan</span><b class="plan-value">{managerSubscription?.plan_name || 'Starter'}</b><p>{managerSubscription?.billing_period || 'Monthly billing'}</p></article></div><div class="dashboard-panels"><article class="panel inventory"><div class="panel-heading"><div><p class="plan-label">Machine control</p><h2>Machine inventory</h2></div><button class="text-button" onclick={() => changePage('machines')}>Open resident view →</button></div>{#each machines as machine}<div class="inventory-row"><div class="machine-symbol small-symbol {machine.type.toLowerCase()}">{machine.icon}</div><div><b>{machine.name}</b><span>{machine.duration} min · ${machine.price.toFixed(2)} per cycle</span></div><span class:available={machine.status === 'Available'} class="status">{machine.status}</span><button class="row-action">Manage</button></div>{/each}</article><article class="panel revenue"><p class="plan-label">Revenue</p><h2>At a glance</h2><div class="revenue-number">${(Number(managerRevenue?.booking_revenue || 0) + Number(managerRevenue?.subscription_revenue || 0)).toFixed(2)}</div><p>Total platform revenue recorded for this building.</p><div class="revenue-bars"><span style="height: 34%"></span><span style="height: 56%"></span><span style="height: 42%"></span><span style="height: 74%"></span><span style="height: 62%"></span><span style="height: 88%"></span><span style="height: 76%"></span></div><button class="outline-button full-width" onclick={exportRevenue}>View full reports</button></article></div>{/if}</section>
	{/if}
</main>

{#if showAuth}<div class="modal-backdrop" transition:fade={{ duration: 160 }} role="presentation"><div class="auth-modal" transition:fly={{ y: 18, duration: 220 }} role="dialog" aria-modal="true"><button class="close" onclick={closeAuth} aria-label="Close">×</button><div class="auth-title"><p class="kicker">{authMode === 'signup' ? 'Resident account' : authAudience === 'manager' ? 'Property workspace' : 'Welcome back'}</p><h2>{authMode === 'signup' ? 'Laundry on your terms.' : authAudience === 'manager' ? 'Manage your building.' : 'Good to see you.'}</h2><p>{authMode === 'signup' ? 'Create your free account in a few quick steps.' : authAudience === 'manager' ? 'Use your developer or admin credentials.' : 'Sign in to book your next laundry time.'}</p></div>{#if authMode === 'signin'}<div class="role-switch"><button class:chosen={authAudience === 'resident'} onclick={() => (authAudience = 'resident')}>Resident</button><button class:chosen={authAudience === 'manager'} onclick={() => (authAudience = 'manager')}>Developer / admin</button></div><label>Email<input type="email" bind:value={email} placeholder={authAudience === 'manager' ? 'admin@property.com' : 'you@example.com'} /></label><label>Password<input type="password" bind:value={password} placeholder="Enter password" /></label><button class="button full-width" onclick={login} disabled={loading}>{loading ? 'Signing in…' : `Sign in as ${authAudience === 'manager' ? 'property team' : 'resident'}`} <span>→</span></button>{#if authAudience === 'resident'}<p class="auth-footer">New to Rinse? <button onclick={() => (authMode = 'signup')}>Create an account</button></p>{/if}{:else}<div class="form-grid"><label>Full name<input bind:value={signup.name} placeholder="Maya Carter" /></label><label>Email<input type="email" bind:value={signup.email} placeholder="maya@email.com" /></label><label>Mobile number<input type="tel" bind:value={signup.phone} placeholder="(555) 000-0000" /></label><label>Building<select bind:value={signup.building}><option value="">Choose your building</option>{#each buildings as building}<option>{building}</option>{/each}</select></label></div><label>Card number <span class="optional">(optional for now)</span><input bind:value={signup.card} inputmode="numeric" placeholder="•••• •••• •••• 1234" /></label><button class="button full-width" onclick={createAccount}>Create resident account <span>→</span></button><p class="auth-footer">Already have an account? <button onclick={() => (authMode = 'signin')}>Sign in</button></p>{/if}{#if message}<p class="form-message">{message}</p>{/if}</div></div>{/if}

{#if showReservation && selectedMachine}<div class="modal-backdrop" transition:fade={{ duration: 160 }} role="presentation"><div class="auth-modal reservation-modal" transition:fly={{ y: 18, duration: 220 }} role="dialog" aria-modal="true"><button class="close" onclick={closeReservation} aria-label="Close">×</button><p class="kicker">Reserve a machine</p><h2>{selectedMachine.name}</h2><div class="reservation-summary"><span class="machine-symbol {selectedMachine.type.toLowerCase()}">{selectedMachine.icon}</span><div><b>{selectedMachine.duration} minute cycle</b><span>Pay now · guaranteed time</span></div><strong>${selectedMachine.price.toFixed(2)}</strong></div><div class="form-grid"><label>Date<input type="date" bind:value={selectedDate} /></label><label>Start time<select bind:value={selectedTime}><option value="">Select a time</option>{#each ['8:00 AM','9:00 AM','10:00 AM','11:00 AM','12:00 PM','1:00 PM','2:00 PM','3:00 PM','4:00 PM','5:00 PM','6:00 PM','7:00 PM'] as time}<option>{time}</option>{/each}</select></label></div><button class="button full-width" onclick={confirmReservation} disabled={loading}>{loading ? 'Confirming…' : `Pay $${selectedMachine.price.toFixed(2)} & reserve`} <span>→</span></button>{#if message}<p class="form-message">{message}</p>{/if}</div></div>{/if}

<style>
	:global(*) { box-sizing: border-box; }
	:global(body) { margin: 0; background: #f7f6f2; color: #1c2925; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
	:global(button), :global(input), :global(select) { font: inherit; } :global(button) { cursor: pointer; } :global(button:disabled) { cursor: not-allowed; opacity: .55; }
	header { height: 78px; padding: 0 clamp(24px, 6vw, 92px); background: rgba(247,246,242,.88); backdrop-filter: blur(14px); border-bottom: 1px solid rgba(28,41,37,.09); display: flex; align-items: center; justify-content: space-between; position: sticky; top: 0; z-index: 20; }
	.brand { background: none; border: 0; padding: 0; display: flex; align-items: center; gap: 8px; color: #1c2925; font-family: Georgia, serif; font-size: 26px; font-weight: 700; letter-spacing: -.8px; }.brand-mark { display: grid; place-items: center; width: 27px; height: 27px; color: #f4f3ed; background: #1f6355; border-radius: 50% 50% 47% 47%; font-family: Georgia, serif; font-size: 20px; line-height: 1; }
	nav, .header-actions { display: flex; align-items: center; gap: 8px; } nav button, .text-button { border: 0; background: none; color: #52605a; padding: 10px 12px; font-size: 14px; transition: color .2s ease, background .2s ease; } nav button:hover, nav button.active, .text-button:hover { color: #1f6355; } nav button.active { font-weight: 700; }.header-actions { gap: 14px; }.user-name { color: #52605a; font-size: 14px; }
	.wrap { width: min(1180px, calc(100% - 48px)); margin: 0 auto; }.page { min-height: calc(100vh - 78px); padding-top: 72px; padding-bottom: 92px; }.hero { display: grid; grid-template-columns: 1.05fr .95fr; gap: clamp(48px, 9vw, 128px); align-items: center; min-height: 600px; padding: 62px 0 84px; }.kicker { margin: 0 0 15px; color: #1f7b68; text-transform: uppercase; letter-spacing: .14em; font-size: 11px; font-weight: 800; }.hero h1, .section-intro h1 { font-family: Georgia, 'Times New Roman', serif; letter-spacing: -.06em; font-weight: 500; color: #192621; }.hero h1 { margin: 0; font-size: clamp(52px, 6vw, 82px); line-height: .99; }.lead { max-width: 490px; margin: 28px 0; color: #607069; font-size: 18px; line-height: 1.65; }.hero-actions { display: flex; align-items: center; gap: 20px; }.button, .outline-button, .icon-button, .card-action, .cancel-button { border-radius: 999px; font-weight: 700; transition: transform .2s ease, box-shadow .2s ease, background .2s ease, border-color .2s ease; }.button { border: 1px solid #1f6355; background: #1f6355; color: white; padding: 14px 21px; box-shadow: 0 6px 18px rgba(31,99,85,.16); }.button span { margin-left: 8px; font-size: 17px; }.button:hover { transform: translateY(-2px); background: #195145; box-shadow: 0 10px 24px rgba(31,99,85,.24); }.button.small { padding: 10px 16px; font-size: 14px; }.button.light { color: #1e302a; background: #f7f6f2; border-color: #f7f6f2; box-shadow: none; }.link-button { padding: 8px 0; border: 0; border-bottom: 1px solid #7a8981; color: #26372f; background: none; }.trust-line { margin-top: 33px; color: #78847f; font-size: 13px; }.trust-line span { color: #1f9a73; margin-right: 7px; }
	.hero-visual { position: relative; overflow: hidden; min-height: 420px; padding: 27px; border-radius: 30px; color: #eef5ef; background: #173f36; box-shadow: 0 24px 54px rgba(22,52,44,.19); }.glow { position: absolute; width: 270px; height: 270px; top: -110px; right: -80px; border-radius: 50%; background: #4aa789; filter: blur(25px); opacity: .72; }.visual-top, .reservation-preview, .availability-row, .mini-machines { position: relative; z-index: 1; }.visual-top { display: flex; justify-content: space-between; align-items: center; color: #d7e8dc; font-size: 13px; }.avatar { display: grid; place-items: center; width: 32px; height: 32px; border: 1px solid rgba(255,255,255,.3); border-radius: 50%; background: #e9ac72; color: #23362f; font-weight: 800; }.visual-title { position: relative; z-index: 1; margin: 64px 0 12px; font-family: Georgia, serif; font-size: 29px; }.reservation-preview { display: grid; grid-template-columns: 44px 1fr auto; gap: 13px; align-items: center; padding: 15px; border: 1px solid rgba(255,255,255,.15); border-radius: 15px; background: rgba(8,31,25,.32); }.machine-dot { display: grid; place-items: center; width: 42px; height: 42px; border-radius: 12px; background: #e4f0b7; color: #245347; font-size: 25px; }.reservation-preview strong, .reservation-preview span { display: block; }.reservation-preview strong { font-size: 14px; }.reservation-preview span { margin-top: 4px; color: #b9cec0; font-size: 12px; }.reservation-preview b { color: #e4f0b7; font-size: 14px; }.availability-row { display: flex; justify-content: space-between; margin: 34px 0 13px; color: #dbece1; font-size: 13px; }.mini-machines { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }.mini-machines div { display: grid; place-items: center; gap: 5px; min-height: 83px; border-radius: 12px; background: rgba(255,255,255,.08); color: #8a9f95; font-size: 11px; }.mini-machines div.open { background: rgba(228,240,183,.15); color: #e4f0b7; }.mini-machines i { font-style: normal; font-size: 23px; }
	.benefits { display: grid; grid-template-columns: .7fr 1.3fr; gap: 90px; padding: 112px 0; border-top: 1px solid #dfe1d9; }.benefits h2, .property-banner h2 { margin: 0; font-family: Georgia, serif; font-weight: 500; font-size: clamp(35px, 4vw, 53px); line-height: 1.05; letter-spacing: -.045em; }.benefit-list { display: grid; grid-template-columns: repeat(3, 1fr); gap: 28px; }.benefit-list article { padding-top: 17px; border-top: 1px solid #aebbb2; }.benefit-list span { color: #1f7b68; font-size: 12px; font-weight: 800; }.benefit-list h3 { margin: 28px 0 10px; font-size: 16px; }.benefit-list p, .property-banner p { color: #65726b; font-size: 14px; line-height: 1.6; }.property-banner { display: grid; grid-template-columns: 1fr 1fr; gap: 90px; margin-bottom: 92px; padding: 54px 58px; border-radius: 23px; background: #dce9cf; }.property-banner p { max-width: 410px; margin: 5px 0 25px; color: #506158; }
	.section-intro { max-width: 610px; }.section-intro h1 { margin: 0; font-size: clamp(43px, 5vw, 65px); line-height: 1.03; }.section-intro > p:not(.kicker) { color: #68766f; font-size: 17px; line-height: 1.6; }.toolbar { display: flex; justify-content: space-between; align-items: center; margin: 50px 0 25px; }.filter-pills, .role-switch { display: inline-flex; padding: 4px; border-radius: 999px; background: #e9ebe5; }.filter-pills button, .role-switch button { border: 0; border-radius: 999px; background: transparent; padding: 9px 15px; color: #65716b; font-size: 13px; }.filter-pills button.selected, .role-switch button.chosen { background: white; color: #1f4940; box-shadow: 0 2px 8px rgba(39,55,48,.08); font-weight: 700; }.icon-button { border: 1px solid #cfd7cf; background: #fbfbf8; color: #40554c; padding: 10px 15px; font-size: 13px; }.icon-button:hover, .outline-button:hover { transform: translateY(-1px); border-color: #1f6355; }.machine-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }.machine-card, .price-card, .panel, .metric-grid article { background: #fbfbf8; border: 1px solid #dee2da; }.machine-card { display: flex; min-height: 267px; flex-direction: column; padding: 21px; border-radius: 17px; transition: transform .25s ease, box-shadow .25s ease; }.machine-card:hover { transform: translateY(-4px); box-shadow: 0 15px 32px rgba(30,52,42,.08); }.machine-card-top { display: flex; align-items: center; justify-content: space-between; }.machine-symbol { display: grid; place-items: center; width: 43px; height: 43px; border-radius: 13px; font-size: 25px; }.machine-symbol.washer { color: #216758; background: #d6ebd6; }.machine-symbol.dryer { color: #a1613c; background: #f2dfc3; }.status { display: inline-block; padding: 6px 9px; color: #8a6652; background: #f5e8d7; border-radius: 99px; font-size: 11px; font-weight: 800; }.status.available { color: #236d55; background: #d8edda; }.machine-card h3 { margin: 26px 0 6px; font-size: 17px; }.machine-card p { margin: 0; color: #748077; font-size: 13px; line-height: 1.5; }.card-action { width: 100%; margin-top: auto; padding: 11px 0 3px; border: 0; border-radius: 0; border-top: 1px solid #e1e5dd; background: none; color: #1e6656; text-align: left; font-size: 13px; }.card-action span { float: right; font-size: 17px; }.card-action:disabled { color: #9ba39e; }
	.empty-state { max-width: 580px; margin: 74px auto; padding: 52px; border: 1px solid #dfe2db; border-radius: 21px; background: #fbfbf8; text-align: center; }.empty-icon { display: grid; place-items: center; width: 58px; height: 58px; margin: 0 auto 22px; border-radius: 17px; background: #dce9cf; color: #286354; font-size: 31px; }.empty-state h2 { margin: 0; font-family: Georgia, serif; font-size: 30px; font-weight: 500; }.empty-state p { max-width: 360px; margin: 13px auto 24px; color: #6e7a73; line-height: 1.6; }.booking-list { display: grid; gap: 12px; margin-top: 50px; }.booking-card { display: grid; grid-template-columns: 1fr auto auto; align-items: center; gap: 30px; padding: 25px 28px; border: 1px solid #dfe2db; border-radius: 16px; background: #fbfbf8; }.confirmed { display: inline-block; padding: 5px 8px; border-radius: 99px; background: #d8edda; color: #236d55; font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: .06em; }.booking-main h2 { margin: 10px 0 5px; font-size: 18px; }.booking-main p, .booking-price span { margin: 0; color: #6d7a73; font-size: 13px; }.booking-price { display: grid; gap: 4px; text-align: right; }.booking-price b { font-size: 19px; }.cancel-button { padding: 9px 14px; border: 1px solid #e1c7bd; background: transparent; color: #aa5644; font-size: 12px; }.cancel-button:hover { background: #fff4ef; }
	.pricing-page { background: #f1f0ea; }.centered { margin: 0 auto; text-align: center; }.centered > p:not(.kicker) { margin: 17px auto 0; }.audience-toggle { display: flex; width: max-content; margin: 42px auto 33px; padding: 5px; border-radius: 999px; background: #dfe3db; }.audience-toggle button { border: 0; border-radius: 999px; padding: 10px 21px; color: #68746d; background: none; font-size: 13px; }.audience-toggle .chosen { background: #1e443a; color: white; box-shadow: 0 3px 10px rgba(23,62,52,.2); }.pricing-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }.price-card { position: relative; display: flex; flex-direction: column; min-height: 475px; padding: 30px; border-radius: 18px; }.price-card.featured { color: #eff6ef; border-color: #1c453a; background: #1c453a; box-shadow: 0 18px 30px rgba(28,69,58,.18); }.popular { position: absolute; top: 20px; right: 20px; padding: 5px 9px; border-radius: 99px; background: #dce9cf; color: #1c453a; font-size: 10px; font-weight: 800; text-transform: uppercase; }.plan-label { margin: 0 0 14px; color: #20806b; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: .13em; }.featured .plan-label { color: #b9dbbd; }.price-card h2, .resident-price h2 { margin: 0; font-family: Georgia, serif; font-size: 29px; font-weight: 500; line-height: 1.11; letter-spacing: -.04em; }.price { margin: 31px 0 8px; }.price b { font-family: Georgia, serif; font-size: 39px; font-weight: 500; }.price span { margin-left: 4px; color: #7a867e; font-size: 13px; }.featured .price span, .featured .price-copy, .featured li { color: #bed0c3; }.price-copy { min-height: 38px; margin: 0; color: #6b786f; font-size: 13px; line-height: 1.5; }.price-card ul { display: grid; gap: 13px; margin: 26px 0; padding: 0; list-style: none; color: #4e5d55; font-size: 13px; }.price-card li::before { content: '✓'; margin-right: 10px; color: #248368; font-weight: 800; }.featured li::before { color: #dce9cf; }.full-width { width: 100%; margin-top: auto; }.outline-button { border: 1px solid #9eb4a8; background: transparent; color: #1e5b4d; padding: 13px 16px; }.featured .button { color: #1d4d40; background: #dce9cf; border-color: #dce9cf; }.pricing-note { margin: 26px 0 0; color: #77837b; text-align: center; font-size: 12px; }.resident-price { display: grid; grid-template-columns: 1.1fr .9fr; align-items: center; gap: 100px; max-width: 900px; margin: 25px auto 0; padding: 50px 0; }.resident-price > div > p:not(.plan-label) { max-width: 470px; color: #647168; line-height: 1.7; }.resident-receipt { padding: 26px; border-radius: 17px; background: #fbfbf8; box-shadow: 0 13px 28px rgba(35,53,43,.08); }.resident-receipt > p { margin: 0 0 22px; color: #89938d; font-size: 12px; text-transform: uppercase; letter-spacing: .1em; }.resident-receipt div { display: flex; justify-content: space-between; margin: 14px 0; color: #637168; font-size: 13px; }.resident-receipt b { color: #25342d; }.resident-receipt hr { border: 0; border-top: 1px solid #e0e4dc; }.resident-receipt .total { color: #26362f; font-size: 15px; }.resident-receipt small { display: block; margin-top: 21px; color: #8a948e; font-size: 11px; line-height: 1.5; }
	.dashboard-heading { display: flex; justify-content: space-between; align-items: end; }.dashboard-heading h1 { margin: 0; font-family: Georgia, serif; font-size: clamp(38px, 4vw, 56px); font-weight: 500; letter-spacing: -.05em; }.dashboard-heading p:not(.kicker) { color: #718078; }.metric-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin: 42px 0 16px; }.metric-grid article { padding: 21px; border-radius: 15px; }.metric-grid span, .metric-grid p { display: block; margin: 0; color: #738178; font-size: 12px; }.metric-grid b { display: block; margin: 17px 0 6px; font-family: Georgia, serif; font-size: 31px; font-weight: 500; }.metric-grid small { color: #8a958f; font-family: Inter, sans-serif; font-size: 12px; }.metric-grid .plan-value { font-size: 23px; }.metric-grid .positive { color: #28735c; }.dashboard-panels { display: grid; grid-template-columns: 1.45fr .75fr; gap: 16px; }.panel { padding: 27px; border-radius: 17px; }.panel-heading { display: flex; justify-content: space-between; align-items: start; }.panel h2 { margin: 0; font-family: Georgia, serif; font-size: 25px; font-weight: 500; }.inventory-row { display: grid; grid-template-columns: 38px 1fr auto auto; align-items: center; gap: 12px; padding: 14px 0; border-top: 1px solid #e2e5de; }.inventory-row:first-of-type { margin-top: 24px; }.inventory-row b, .inventory-row span { display: block; }.inventory-row b { font-size: 13px; }.inventory-row div + div span { margin-top: 4px; color: #7b877f; font-size: 11px; }.small-symbol { width: 34px; height: 34px; border-radius: 10px; font-size: 19px; }.row-action { border: 0; background: none; color: #1f705d; font-size: 12px; }.revenue { background: #dce9cf; border-color: #dce9cf; }.revenue-number { margin: 35px 0 5px; font-family: Georgia, serif; font-size: 47px; }.revenue > p:not(.plan-label) { color: #5c7065; font-size: 13px; line-height: 1.5; }.revenue-bars { display: flex; align-items: end; height: 105px; gap: 8px; margin: 22px 0; }.revenue-bars span { flex: 1; border-radius: 4px 4px 0 0; background: #619783; }.revenue-bars span:nth-child(2n) { background: #357462; }.revenue .outline-button { border-color: #83aa98; }
	.notice { position: fixed; top: 90px; left: 50%; z-index: 40; display: flex; align-items: center; gap: 9px; width: min(510px, calc(100% - 40px)); padding: 12px 15px; border: 1px solid #b4d2bf; border-radius: 11px; background: #eef7ed; color: #285e4c; box-shadow: 0 10px 24px rgba(28,56,44,.12); transform: translateX(-50%); font-size: 13px; font-weight: 600; }.notice > span { color: #298466; }.notice button { margin-left: auto; border: 0; background: none; color: #628275; font-size: 21px; }.modal-backdrop { position: fixed; inset: 0; z-index: 50; display: grid; place-items: center; padding: 24px; background: rgba(17,35,29,.48); backdrop-filter: blur(5px); }.auth-modal { position: relative; width: min(490px, 100%); max-height: min(760px, calc(100vh - 48px)); overflow: auto; padding: 34px; border-radius: 22px; background: #fbfbf8; box-shadow: 0 26px 80px rgba(12,29,23,.32); }.close { position: absolute; top: 15px; right: 17px; border: 0; background: none; color: #607168; font-size: 27px; }.auth-title h2 { margin: 0; font-family: Georgia, serif; font-size: 34px; font-weight: 500; letter-spacing: -.04em; }.auth-title > p:not(.kicker) { margin: 10px 0 23px; color: #718077; font-size: 14px; line-height: 1.55; }.role-switch { margin-bottom: 22px; }.role-switch button { flex: 1; }.auth-modal label { display: block; margin: 15px 0 0; color: #44534c; font-size: 12px; font-weight: 700; }.auth-modal input, .auth-modal select { display: block; width: 100%; margin-top: 7px; padding: 12px 13px; border: 1px solid #d1d9d1; border-radius: 9px; outline: 0; background: white; color: #293a32; font-size: 14px; transition: border-color .2s ease, box-shadow .2s ease; }.auth-modal input:focus, .auth-modal select:focus { border-color: #398270; box-shadow: 0 0 0 3px rgba(57,130,112,.12); }.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0 12px; }.optional { color: #98a29b; font-weight: 500; }.auth-footer { margin: 19px 0 0; color: #718077; text-align: center; font-size: 12px; }.auth-footer button { border: 0; border-bottom: 1px solid #87a397; background: none; color: #20725e; font-weight: 700; }.form-message { margin: 15px 0 0; padding: 10px; border-radius: 8px; background: #eef5eb; color: #3d6e59; font-size: 12px; line-height: 1.45; }.reservation-modal h2 { margin: 0 0 22px; font-family: Georgia, serif; font-size: 33px; font-weight: 500; }.reservation-summary { display: grid; grid-template-columns: 43px 1fr auto; gap: 12px; align-items: center; margin-bottom: 20px; padding: 14px; border-radius: 13px; background: #edf3e8; }.reservation-summary b, .reservation-summary span { display: block; }.reservation-summary b { font-size: 13px; }.reservation-summary span { margin-top: 4px; color: #6a7b70; font-size: 11px; }.reservation-summary strong { color: #1c5e4e; }
	@media (max-width: 900px) { header { padding: 0 24px; } nav { display: none; }.hero { grid-template-columns: 1fr; gap: 45px; }.hero-visual { max-width: 570px; width: 100%; }.benefits, .property-banner, .resident-price, .dashboard-panels { grid-template-columns: 1fr; gap: 36px; }.benefit-list { gap: 16px; }.machine-grid { grid-template-columns: repeat(2, 1fr); }.pricing-grid { grid-template-columns: 1fr; max-width: 500px; margin: auto; }.price-card { min-height: auto; }.metric-grid { grid-template-columns: repeat(2, 1fr); }.property-banner { padding: 40px; } }
	@media (max-width: 560px) { header { height: 68px; }.brand { font-size: 23px; }.header-actions .text-button { display: none; }.page { padding-top: 50px; }.wrap { width: min(100% - 32px, 1180px); }.hero { min-height: auto; padding: 50px 0 64px; }.hero h1 { font-size: 52px; }.hero-actions { align-items: start; flex-direction: column; gap: 17px; }.hero-visual { min-height: 370px; }.benefits { padding: 70px 0; }.benefit-list { grid-template-columns: 1fr; }.property-banner { margin-bottom: 60px; padding: 32px; }.toolbar, .dashboard-heading { align-items: start; flex-direction: column; gap: 16px; }.filter-pills { overflow-x: auto; max-width: 100%; }.machine-grid { grid-template-columns: 1fr; }.booking-card { grid-template-columns: 1fr auto; gap: 18px; }.booking-card .cancel-button { grid-column: 1 / -1; width: 100%; }.metric-grid { grid-template-columns: 1fr 1fr; }.metric-grid article { padding: 16px; }.inventory-row { grid-template-columns: 34px 1fr auto; }.inventory-row .row-action { display: none; }.auth-modal { padding: 28px 22px; }.form-grid { grid-template-columns: 1fr; }.reservation-summary { grid-template-columns: 43px 1fr; }.reservation-summary strong { grid-column: 2; }.resident-price { padding-top: 20px; }.price-card { padding: 26px; } }
</style>
