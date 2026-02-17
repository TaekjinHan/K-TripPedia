/**
 * KakaoMap 래퍼 -- dynamic import(ssr:false)로 CSR 전용 로딩
 *
 * 사용법:
 * import KakaoMapDynamic from '@/components/KakaoMapDynamic';
 * <KakaoMapDynamic center={{ lat: 37.5596, lng: 126.9851 }} level={4} />
 */
import dynamic from 'next/dynamic';

export interface KakaoMapProps {
    center?: { lat: number; lng: number };
    level?: number;
    className?: string;
    /** 마커를 표시할 장소 배열 */
    places?: MarkerData[];
    /** 마커 클릭 시 콜백 */
    onMarkerClick?: (placeId: string) => void;
}

export interface MarkerData {
    id: string;
    lat: number;
    lng: number;
    name_ko: string;
    solo_ok_level: 'HIGH' | 'MID' | 'LOW';
}

const KakaoMapDynamic = dynamic<KakaoMapProps>(
    () => import('./KakaoMapView'),
    {
        ssr: false,
        loading: () => (
            <div
                style={{
                    width: '100%',
                    height: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    background: 'var(--color-bg-secondary)',
                    color: 'var(--color-text-muted)',
                    fontSize: 'var(--font-size-sm)',
                }}
            >
                지도 로딩중...
            </div>
        ),
    }
);

export default KakaoMapDynamic;
