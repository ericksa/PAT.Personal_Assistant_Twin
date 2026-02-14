<template>
  <div class="app-container">
    <nav class="navbar">
      <div class="nav-brand">PAT Manager</div>
      <div class="nav-links">
        <router-link to="/">Dashboard</router-link>
        <router-link to="/chat">Chat</router-link>
      </div>
    </nav>
    <main class="content">
      <router-view></router-view>
    </main>
  </div>
</template>

<style scoped>
.app-container {
  font-family: Arial, sans-serif;
}
.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  background-color: #2c3e50;
  color: white;
}
.nav-links a {
  color: white;
  margin-left: 1rem;
  text-decoration: none;
}
.nav-links a.router-link-active {
  font-weight: bold;
  border-bottom: 2px solid #42b983;
}
.content {
  padding: 2rem;
}
</style>
