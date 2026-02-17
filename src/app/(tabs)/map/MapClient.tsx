/**
 * MapClient -- 지도 탭 클라이언트 컴포넌트
 *
 * Supabase에서 places + solo_profile을 가져와서
 * 카카오맵 위에 Confidence 컬러 핀으로 표시
 * 핀 클릭 -> 하단 PlaceCard -> 상세 페이지 링크
 */
'use client';

import { useEffect, useState, useCallback } from 'react';
import { supabase } from '@/lib/supabase';
import KakaoMapDynamic from '@/components/KakaoMapDynamic';
import type { MarkerData } from '@/components/KakaoMapDynamic';
import PlaceCard from '@/components/PlaceCard';
import type { PlaceCardData } from '@/components/PlaceCard';
import type { SoloOkLevel, SoloAllowed } from '@/lib/types';
import { useTranslation } from '@/hooks/useTranslation';
import styles from './MapClient.module.css';

interface PlaceRow {
    id: string;
    name_ko: string;
    name_ja: string | null;
    category: string;
    address: string;
    lat: number;
    lng: number;
    solo_profile: {
        solo_ok_level: SoloOkLevel;
        solo_allowed: SoloAllowed;
        min_portions_required: number | null;
        counter_seat: string | null;
        best_time_note: string | null;
    } | null;
}

export default function MapClient() {
    const t = useTranslation();
    const [markers, setMarkers] = useState<MarkerData[]>([]);
    const [placeMap, setPlaceMap] = useState<Map<string, PlaceCardData>>(new Map());
    const [selectedId, setSelectedId] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    /** Supabase에서 places + solo_profile을 가져오기 */
    useEffect(() => {
        const fetchPlaces = async () => {
            setLoading(true);
            setError(null);

            const { data, error: fetchErr } = await supabase
                .from('places')
                .select(`
          id,
          name_ko,
          name_ja,
          category,
          address,
          lat,
          lng,
          solo_profile (
            solo_ok_level,
            solo_allowed,
            min_portions_required,
            counter_seat,
            best_time_note
          )
        `)
                .order('name_ko');

            if (fetchErr) {
                console.error('[MapClient] Fetch error:', fetchErr);
                setError(fetchErr.message);
                setLoading(false);
                return;
            }

            const rows = (data ?? []) as unknown as PlaceRow[];

            // 마커 데이터 변환
            const markerList: MarkerData[] = rows.map((r) => ({
                id: r.id,
                lat: r.lat,
                lng: r.lng,
                name_ko: r.name_ko,
                solo_ok_level: r.solo_profile?.solo_ok_level ?? 'LOW',
            }));

            // PlaceCard용 참조 맵
            const cardMap = new Map<string, PlaceCardData>();
            rows.forEach((r) => {
                cardMap.set(r.id, {
                    id: r.id,
                    name_ko: r.name_ko,
                    name_ja: r.name_ja,
                    category: r.category,
                    address: r.address,
                    solo_ok_level: r.solo_profile?.solo_ok_level ?? 'LOW',
                    solo_allowed: r.solo_profile?.solo_allowed ?? 'YES',
                    min_portions_required: r.solo_profile?.min_portions_required ?? null,
                    counter_seat: r.solo_profile?.counter_seat ?? null,
                    best_time_note: r.solo_profile?.best_time_note ?? null,
                });
            });

            setMarkers(markerList);
            setPlaceMap(cardMap);
            setLoading(false);
        };

        fetchPlaces();
    }, []);

    const handleMarkerClick = useCallback((placeId: string) => {
        setSelectedId(placeId);
    }, []);

    const handleCloseCard = useCallback(() => {
        setSelectedId(null);
    }, []);

    const selectedPlace = selectedId ? placeMap.get(selectedId) : null;

    return (
        <div className={styles.container}>
            {/* 상단 헤더 */}
            <div className={styles.header}>
                <span className={styles.title}>{t('map.title')}</span>
                <span className={styles.count}>
                    {loading ? '...' : `${markers.length}${t('map.countSuffix')}`}
                </span>
            </div>

            {/* 에러 표시 */}
            {error && (
                <div className={styles.error}>{t('map.loadError')}</div>
            )}

            {/* 지도 */}
            <div className={styles.mapArea}>
                <KakaoMapDynamic
                    places={markers}
                    onMarkerClick={handleMarkerClick}
                    className={styles.map}
                />
            </div>

            {/* 선택된 장소 카드 */}
            {selectedPlace && (
                <div className={styles.cardOverlay}>
                    <PlaceCard place={selectedPlace} onClose={handleCloseCard} />
                </div>
            )}
        </div>
    );
}
