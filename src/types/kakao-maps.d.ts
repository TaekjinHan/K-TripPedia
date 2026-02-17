/**
 * Kakao Maps JavaScript API 전역 타입 선언
 * PoC 단계에서 사용하는 API만 최소 선언
 */

declare namespace kakao {
    namespace maps {
        function load(callback: () => void): void;

        class Map {
            constructor(container: HTMLElement, options: MapOptions);
            setCenter(latlng: LatLng): void;
            setLevel(level: number): void;
            getCenter(): LatLng;
            getLevel(): number;
            panTo(latlng: LatLng): void;
            relayout(): void;
        }

        class LatLng {
            constructor(lat: number, lng: number);
            getLat(): number;
            getLng(): number;
        }

        class Marker {
            constructor(options?: MarkerOptions);
            setMap(map: Map | null): void;
            setPosition(position: LatLng): void;
            getPosition(): LatLng;
            setImage(image: MarkerImage): void;
        }

        class MarkerImage {
            constructor(
                src: string,
                size: Size,
                options?: { offset?: Point; shape?: string; coords?: string }
            );
        }

        class InfoWindow {
            constructor(options?: InfoWindowOptions);
            open(map: Map, marker: Marker): void;
            close(): void;
            setContent(content: string | HTMLElement): void;
            getContent(): string;
        }

        class CustomOverlay {
            constructor(options?: CustomOverlayOptions);
            setMap(map: Map | null): void;
            setPosition(position: LatLng): void;
            setContent(content: string | HTMLElement): void;
            getPosition(): LatLng;
        }

        class Size {
            constructor(width: number, height: number);
        }

        class Point {
            constructor(x: number, y: number);
        }

        class LatLngBounds {
            constructor(sw?: LatLng, ne?: LatLng);
            extend(latlng: LatLng): void;
        }

        namespace event {
            function addListener(
                target: unknown,
                type: string,
                handler: (...args: unknown[]) => void
            ): void;
            function removeListener(
                target: unknown,
                type: string,
                handler: (...args: unknown[]) => void
            ): void;
        }

        interface MapOptions {
            center: LatLng;
            level?: number;
            mapTypeId?: unknown;
            draggable?: boolean;
            scrollwheel?: boolean;
            disableDoubleClick?: boolean;
            disableDoubleClickZoom?: boolean;
        }

        interface MarkerOptions {
            map?: Map;
            position?: LatLng;
            title?: string;
            image?: MarkerImage;
            clickable?: boolean;
            zIndex?: number;
        }

        interface InfoWindowOptions {
            content?: string | HTMLElement;
            position?: LatLng;
            removable?: boolean;
            zIndex?: number;
        }

        interface CustomOverlayOptions {
            map?: Map;
            position?: LatLng;
            content?: string | HTMLElement;
            xAnchor?: number;
            yAnchor?: number;
            zIndex?: number;
            clickable?: boolean;
        }
    }
}

interface Window {
    kakao: typeof kakao;
}
