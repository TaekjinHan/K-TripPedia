import PlaceDetailClient from './PlaceDetailClient';
import type { Metadata } from 'next';
import { supabaseServer } from '@/lib/supabaseServer';

/**
 * 장소 상세 페이지 -- PlaceDetailClient(클라이언트 컴포넌트)를 렌더
 * Dynamic Route: /place/[id]
 */
export async function generateMetadata(
    { params }: { params: Promise<{ id: string }> }
): Promise<Metadata> {
    const { id } = await params;

    const { data: place } = await supabaseServer
        .from('places')
        .select('name_ko, name_ja, category, address')
        .eq('id', id)
        .single();

    if (!place) {
        return {
            title: 'お店情報 | ひとりOK',
            description: '韓国ひとり飯ガイド ひとりOKのお店詳細情報です。',
        };
    }

    const displayName = place.name_ja || place.name_ko;
    const title = `${displayName} | ひとりOK`;
    const description = `${place.address}の${displayName}。韓国ひとり飯の体験レポートと注意点を確認できます。`;

    return {
        title,
        description,
        openGraph: {
            title,
            description,
            type: 'article',
        },
        twitter: {
            card: 'summary',
            title,
            description,
        },
    };
}

export default function PlaceDetailPage() {
    return <PlaceDetailClient />;
}
