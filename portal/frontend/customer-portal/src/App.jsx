// Legacy shim file.
// The real GuardDuty app (no-login landing + routing) lives in App.tsx.
// If anything accidentally imports App.jsx, we still render the correct app.

import App from "./App.tsx";

export default App;
