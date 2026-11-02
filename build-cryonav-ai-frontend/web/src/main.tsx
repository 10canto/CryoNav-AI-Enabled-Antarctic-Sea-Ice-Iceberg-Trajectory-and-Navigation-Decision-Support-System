import { createRoot } from 'react-dom/client';
import App from './App';
import './styles.css';

// StrictMode is intentionally not used: its dev-only double effect run would
// create (and destroy) a second Leaflet map, which the "map instances = 1" check forbids.
createRoot(document.getElementById('root')!).render(<App />);
