'use client';
import { useEffect, useRef } from 'react';

interface CityData {
  name?: string;
  city?: string;
  aqi: number;
  pm25: number;
  pm10: number;
  temperature: number;
  humidity: number;
}

interface Props {
  cities: CityData[];
}

const CITY_COORDS: Record<string, { lat: number; lng: number }> = {
  Mumbai:    { lat: 19.0760, lng: 72.8777 },
  Delhi:     { lat: 28.6139, lng: 77.2090 },
  Bangalore: { lat: 12.9716, lng: 77.5946 },
  Chennai:   { lat: 13.0827, lng: 80.2707 },
  Kolkata:   { lat: 22.5726, lng: 88.3639 },
  Hyderabad: { lat: 17.3850, lng: 78.4867 },
};

function getAqiColor(aqi: number): string {
  if (aqi <= 50)  return '#22c55e';
  if (aqi <= 100) return '#eab308';
  if (aqi <= 150) return '#f97316';
  if (aqi <= 200) return '#ef4444';
  return '#a855f7';
}

declare global {
  interface Window { google: any; initAirSenseMap: () => void; }
}

export default function HeatmapView({ cities }: Props) {
  const mapRef  = useRef<HTMLDivElement>(null);
  const mapInst = useRef<any>(null);
  const markers = useRef<any[]>([]);
  const heatmap = useRef<any>(null);

  // Get city name whether field is 'city' or 'name'
  function getCityName(c: CityData): string {
    return c.city || c.name || '';
  }

  useEffect(() => {
    const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_KEY;
    if (!apiKey) return;

    if (!document.getElementById('gmaps-script')) {
      window.initAirSenseMap = initMap;
      const s = document.createElement('script');
      s.id  = 'gmaps-script';
      s.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=visualization&callback=initAirSenseMap`;
      s.async = true;
      document.head.appendChild(s);
    } else if (window.google?.maps) {
      initMap();
    }
  }, []);

  useEffect(() => {
    if (mapInst.current && window.google) updateMap();
  }, [cities]);

  function initMap() {
    if (!mapRef.current) return;
    mapInst.current = new window.google.maps.Map(mapRef.current, {
      center: { lat: 20.5937, lng: 78.9629 },
      zoom: 5,
      mapTypeId: 'roadmap',
      styles: [
        { elementType: 'geometry',           stylers: [{ color: '#0f172a' }] },
        { elementType: 'labels.text.fill',   stylers: [{ color: '#94a3b8' }] },
        { elementType: 'labels.text.stroke', stylers: [{ color: '#0f172a' }] },
        { featureType: 'water', elementType: 'geometry', stylers: [{ color: '#0e1626' }] },
        { featureType: 'road',  elementType: 'geometry', stylers: [{ color: '#1e3a5f' }] },
        { featureType: 'poi',   stylers: [{ visibility: 'off' }] },
      ],
    });
    updateMap();
  }

  function updateMap() {
    if (!mapInst.current || !window.google) return;

    markers.current.forEach(m => m.setMap(null));
    markers.current = [];
    if (heatmap.current) heatmap.current.setMap(null);

    const validCities = cities.filter(c => CITY_COORDS[getCityName(c)]);

    heatmap.current = new window.google.maps.visualization.HeatmapLayer({
      data: validCities.map(c => ({
        location: new window.google.maps.LatLng(
          CITY_COORDS[getCityName(c)].lat,
          CITY_COORDS[getCityName(c)].lng
        ),
        weight: c.aqi / 50,
      })),
      map: mapInst.current,
      radius: 80,
      opacity: 0.75,
      gradient: [
        'rgba(0,228,0,0)',   'rgba(0,228,0,1)',
        'rgba(255,255,0,1)', 'rgba(255,126,0,1)',
        'rgba(255,0,0,1)',   'rgba(143,63,151,1)',
        'rgba(126,0,35,1)',
      ],
    });

    validCities.forEach(city => {
      const name   = getCityName(city);
      const coords = CITY_COORDS[name];
      const color  = getAqiColor(city.aqi);

      const marker = new window.google.maps.Marker({
        position: coords,
        map: mapInst.current,
        title: name,
        icon: {
          path: window.google.maps.SymbolPath.CIRCLE,
          scale: 14,
          fillColor: color,
          fillOpacity: 0.9,
          strokeColor: '#ffffff',
          strokeWeight: 2,
        },
      });

      const info = new window.google.maps.InfoWindow({
        content: `
          <div style="background:#1e293b;color:#e2e8f0;padding:14px;
            border-radius:10px;min-width:160px;font-family:system-ui;
            border:1px solid ${color}">
            <div style="font-weight:700;font-size:15px;margin-bottom:8px">📍 ${name}</div>
            <div style="font-size:28px;font-weight:800;color:${color}">
              ${Math.round(city.aqi)}
              <span style="font-size:13px;font-weight:400;color:#94a3b8">AQI</span>
            </div>
            <div style="font-size:12px;color:#94a3b8;margin-top:8px;
              display:grid;grid-template-columns:1fr 1fr;gap:4px">
              <div>PM2.5: <b style="color:#e2e8f0">${city.pm25?.toFixed(1)}</b></div>
              <div>PM10: <b style="color:#e2e8f0">${city.pm10?.toFixed(1)}</b></div>
              <div>Temp: <b style="color:#e2e8f0">${city.temperature?.toFixed(0)}°C</b></div>
              <div>Humidity: <b style="color:#e2e8f0">${city.humidity?.toFixed(0)}%</b></div>
            </div>
          </div>`,
      });

      marker.addListener('click', () => info.open(mapInst.current, marker));
      markers.current.push(marker);
    });
  }

  if (!process.env.NEXT_PUBLIC_GOOGLE_MAPS_KEY) {
    return (
      <div style={{ background: '#1e293b', borderRadius: '12px', padding: '40px',
        textAlign: 'center', border: '1px solid #334155' }}>
        <div style={{ fontSize: '40px', marginBottom: '12px' }}>🗺️</div>
        <div style={{ color: '#e2e8f0', fontWeight: 600, marginBottom: '8px' }}>
          Add NEXT_PUBLIC_GOOGLE_MAPS_KEY to .env.local
        </div>
      </div>
    );
  }

  return (
    <div style={{ borderRadius: '12px', overflow: 'hidden', border: '1px solid #334155', position: 'relative' }}>
      <div ref={mapRef} style={{ width: '100%', height: '500px' }} />
      <div style={{ position: 'absolute', bottom: '12px', left: '12px',
        background: 'rgba(15,23,42,0.9)', borderRadius: '8px',
        padding: '8px 12px', fontSize: '11px', color: '#94a3b8' }}>
        Click any marker for details
      </div>
    </div>
  );
}