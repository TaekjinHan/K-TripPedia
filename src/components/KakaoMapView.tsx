'use client';

import { useEffect, useRef, useCallback, useState } from 'react';
import type { KakaoMapProps } from './KakaoMapDynamic';
import { DEFAULT_CENTER, DEFAULT_ZOOM } from '@/lib/constants';
import { CONFIDENCE_COLORS } from '@/lib/constants';

type MapStatus = 'loading' | 'ready' | 'error';

/**
 * Kakao Maps JavaScript API를 사용하는 지도 뷰
 * 반드시 KakaoMapDynamic(dynamic import, ssr:false)을 통해 로딩할 것
 */
export default function KakaoMapView({
    center = DEFAULT_CENTER,
    level = DEFAULT_ZOOM,
    className,
    places = [],
    onMarkerClick,
}: KakaoMapProps) {
    const mapRef = useRef<HTMLDivElement>(null);
    const mapInstanceRef = useRef<kakao.maps.Map | null>(null);
    const markersRef = useRef<kakao.maps.Marker[]>([]);
    const [status, setStatus] = useState<MapStatus>('loading');
    const [errorMsg, setErrorMsg] = useState('');

    /** 기존 마커 전부 제거 */
    const clearMarkers = useCallback(() => {
        markersRef.current.forEach((m) => m.setMap(null));
        markersRef.current = [];
    }, []);

    /** Confidence 레벨에 맞는 SVG 마커 이미지 생성 */
    const createMarkerImage = useCallback((soloOkLevel: 'HIGH' | 'MID' | 'LOW') => {
        const color = CONFIDENCE_COLORS[soloOkLevel] || CONFIDENCE_COLORS.LOW;
        const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="28" height="36" viewBox="0 0 28 36"><path d="M14 0C6.27 0 0 6.27 0 14c0 10.5 14 22 14 22s14-11.5 14-22C28 6.27 21.73 0 14 0z" fill="${color}" stroke="#fff" stroke-width="1.5"/><circle cx="14" cy="13" r="5" fill="#fff"/></svg>`;
        const encoded = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
        return new kakao.maps.MarkerImage(
            encoded,
            new kakao.maps.Size(28, 36),
            { offset: new kakao.maps.Point(14, 36) }
        );
    }, []);

    /** 마커 배치 */
    const renderMarkers = useCallback(
        (map: kakao.maps.Map) => {
            clearMarkers();

            places.forEach((place) => {
                const position = new kakao.maps.LatLng(place.lat, place.lng);
                const markerImage = createMarkerImage(place.solo_ok_level);

                const marker = new kakao.maps.Marker({
                    map,
                    position,
                    title: place.name_ko,
                    image: markerImage,
                    clickable: true,
                });

                kakao.maps.event.addListener(marker, 'click', () => {
                    onMarkerClick?.(place.id);
                });

                markersRef.current.push(marker);
            });
        },
        [places, onMarkerClick, clearMarkers, createMarkerImage],
    );

    /** 지도 초기화 */
    useEffect(() => {
        if (!mapRef.current) return;

        const kakaoKey = process.env.NEXT_PUBLIC_KAKAO_MAP_KEY;
        if (!kakaoKey || kakaoKey === 'your-kakao-javascript-key') {
            setStatus('error');
            setErrorMsg('NEXT_PUBLIC_KAKAO_MAP_KEY가 설정되지 않았습니다');
            return;
        }

        const initMap = () => {
            try {
                kakao.maps.load(() => {
                    if (!mapRef.current) return;

                    const map = new kakao.maps.Map(mapRef.current, {
                        center: new kakao.maps.LatLng(center.lat, center.lng),
                        level,
                    });

                    mapInstanceRef.current = map;
                    setStatus('ready');

                    // 컨테이너 리사이즈 후 relayout 호출 (높이 0 방지)
                    setTimeout(() => {
                        map.relayout();
                    }, 100);

                    renderMarkers(map);
                });
            } catch (e) {
                console.error('[KakaoMapView] init error:', e);
                setStatus('error');
                setErrorMsg('지도 초기화에 실패했습니다');
            }
        };

        // SDK 스크립트가 이미 존재하는지 확인
        const existingScript = document.querySelector(
            'script[src*="dapi.kakao.com"]',
        ) as HTMLScriptElement | null;

        if (existingScript) {
            if (window.kakao && window.kakao.maps) {
                initMap();
            } else {
                existingScript.addEventListener('load', initMap);
            }
            return;
        }

        // SDK 동적 삽입
        const script = document.createElement('script');
        script.src = `//dapi.kakao.com/v2/maps/sdk.js?appkey=${kakaoKey}&autoload=false`;
        script.async = true;

        script.onload = () => {
            initMap();
        };

        script.onerror = () => {
            setStatus('error');
            setErrorMsg('Kakao Maps SDK 로딩 실패 -- API 키 또는 플랫폼 등록을 확인하세요');
        };

        document.head.appendChild(script);

        return () => {
            clearMarkers();
            mapInstanceRef.current = null;
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [center.lat, center.lng, level]);

    /** places가 변경되면 마커만 다시 그리기 */
    useEffect(() => {
        if (mapInstanceRef.current) {
            renderMarkers(mapInstanceRef.current);
        }
    }, [places, renderMarkers]);

    return (
        <div
            ref={mapRef}
            className={className}
            style={{
                width: '100%',
                height: '100%',
                minHeight: '300px',
                background: '#f0f0f0',
                position: 'relative',
            }}
        >
            {status === 'loading' && (
                <div style={{
                    position: 'absolute',
                    inset: 0,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#94A3B8',
                    fontSize: '14px',
                    zIndex: 1,
                }}>
                    지도 로딩중...
                </div>
            )}
            {status === 'error' && (
                <div style={{
                    position: 'absolute',
                    inset: 0,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#EF4444',
                    fontSize: '14px',
                    gap: '8px',
                    padding: '16px',
                    textAlign: 'center',
                    zIndex: 1,
                }}>
                    <span style={{ fontWeight: 600 }}>지도를 표시할 수 없습니다</span>
                    <span style={{ color: '#94A3B8', fontSize: '12px' }}>{errorMsg}</span>
                </div>
            )}
        </div>
    );
}
