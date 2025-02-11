import React, { useState, useEffect } from 'react';
import { GoogleMap, LoadScript, Marker, Autocomplete } from '@react-google-maps/api';
import { Form } from 'react-bootstrap';
import { renderToStaticMarkup } from 'react-dom/server';
import { MyLocation } from '@mui/icons-material';
import L from 'leaflet';


const libraries = ["places"];

const MapContainer = ({ selectedLocation, onLocationSelect, address }) => {
    const [currentPosition, setCurrentPosition] = useState(null);
    const [autocomplete, setAutocomplete] = useState(address);
    const [addressName, setAddress] = useState(address);
    const [error, setError] = useState(null);

    useEffect(() => {
        const getCurrentLocation = () => {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    position => {
                        const { latitude, longitude } = position.coords;
                        setCurrentPosition({ lat: latitude, lng: longitude });
                    },
                    error => {
                        console.error('Error getting user location:', error);
                        setError('Error obteniendo la ubicación del usuario.');
                    }
                );
            } else {
                console.error('Geolocation is not supported by this browser.');
                setError('La geolocalización no es compatible con este navegador.');
            }
        };

        getCurrentLocation();
    }, []);

    const handleAutocompleteLoad = autocomplete => {
        setAutocomplete(autocomplete);
    };

    const myLocationIcon = L.divIcon({
        className: 'my-location-icon',
        html: renderToStaticMarkup(<MyLocation color='primary' />),
    });

    const handlePlaceChanged = () => {
        if (autocomplete !== null) {
            const place = autocomplete.getPlace();
            if (!place.geometry) {
                setError('Lugar no encontrado.');
                return;
            } else {
                setError(null);
            }
            const location = {
                lat: place.geometry.location.lat(),
                lng: place.geometry.location.lng()
            };
            setCurrentPosition(location);
            onLocationSelect({
                location, address: {
                    address: place.formatted_address,
                    name: place.name
                }
            });
        } else {
            setError('Autocompletado aún no cargado.');
        }
    };

    return (
        <LoadScript
            googleMapsApiKey={process.env.GOOGLE_API}
            libraries={libraries}
        >
            <GoogleMap
                mapContainerStyle={mapStyles}
                zoom={13}
                center={selectedLocation || currentPosition || { lat: 0, lng: 0 }}
                options={mapOptions}
            >
                {selectedLocation && <Marker position={selectedLocation} />}
                {onLocationSelect && <Autocomplete onLoad={handleAutocompleteLoad} onPlaceChanged={handlePlaceChanged}>
                    <Form.Control type="text" placeholder="Buscar lugares cerca..." style={searchStyles} defaultValue={address} />
                </Autocomplete>}
            </GoogleMap>
            {error && <div className="alert alert-danger mt-3" role="alert">{error}</div>}
        </LoadScript>
    );
};

const mapStyles = {
    height: "200px",
    width: "100%",
    borderRadius: "10px",
    boxShadow: "0 4px 8px rgba(0, 0, 0, 0.1)"
};

const mapOptions = {
    disableDefaultUI: true
};

const searchStyles = {
    position: "absolute",
    top: "10px",
    left: "50%",
    transform: "translateX(-50%)",
    width: "240px",
    borderRadius: "5px",
    boxShadow: "0 2px 6px rgba(0, 0, 0, 0.3)",
    backgroundColor: "#ffffff",
    color: "#000000"
};


export default MapContainer;
