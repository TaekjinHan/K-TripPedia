import ReportClient from './ReportClient';
import type { Metadata } from 'next';
import { supabaseServer } from '@/lib/supabaseServer';

/**
 * 리포트 페이지 -- ReportClient(클라이언트 컴포넌트)를 렌더
 * Dynamic Route: /report/[id]
 */
export async function generateMetadata(
    { params }: { params: Promise<{ id: string }> }
): Promise<Metadata> {
    const { id } = await params;

    const { data: place } = await supabaseServer
        .from('places')
        .select('name_ko, name_ja, address')
        .eq('id', id)
        .single();

    if (!place) {
        return {
            title: '体験レポート投稿 | ひとりOK',
            description: '韓国ひとり飯の体験を投稿して、最新情報を共有しましょう。',
        };
    }

    const displayName = place.name_ja || place.name_ko;
    const title = `${displayName} 体験レポート投稿 | ひとりOK`;
    const description = `${place.address}の${displayName}に関するひとり飯体験を投稿するページです。`;

    return {
        title,
        description,
        openGraph: {
            title,
            description,
            type: 'website',
        },
        twitter: {
            card: 'summary',
            title,
            description,
        },
    };
}

export default function ReportPage() {
    return <ReportClient />;
}
