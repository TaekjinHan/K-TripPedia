import type { MetadataRoute } from 'next';

/**
 * PWA Manifest -- App Router 내장 방식
 * Next.js가 자동으로 /manifest.webmanifest 으로 서빙합니다.
 */
export default function manifest(): MetadataRoute.Manifest {
    return {
        name: 'ひとりOK',
        short_name: 'ひとりOK',
        description: '韓国で一人ご飯できるお店を見つけよう',
        start_url: '/map',
        display: 'standalone',
        background_color: '#FFFFFF',
        theme_color: '#2563EB',
        orientation: 'portrait',
        icons: [
            {
                src: '/icons/icon-192.png',
                sizes: '192x192',
                type: 'image/png',
            },
            {
                src: '/icons/icon-512.png',
                sizes: '512x512',
                type: 'image/png',
            },
        ],
    };
}
