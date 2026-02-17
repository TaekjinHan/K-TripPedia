'use client';

import { usePathname } from 'next/navigation';
import Link from 'next/link';
import styles from './BottomTabBar.module.css';
import { useTranslation } from '@/hooks/useTranslation';

interface TabItem {
    key: string;
    href: string;
    labelKey: string;
}

const TABS: TabItem[] = [
    { key: 'map', href: '/map', labelKey: 'tabs.map' },
    { key: 'list', href: '/list', labelKey: 'tabs.list' },
    { key: 'pass', href: '/pass', labelKey: 'tabs.pass' },
    { key: 'saved', href: '/saved', labelKey: 'tabs.saved' },
    { key: 'my', href: '/my', labelKey: 'tabs.my' },
];

/** SVG 아이콘 -- 가벼운 인라인 아이콘 */
function TabIcon({ tabKey, active }: { tabKey: string; active: boolean }) {
    const color = active ? 'var(--color-primary)' : 'var(--color-text-muted)';
    const size = 24;

    switch (tabKey) {
        case 'map':
            return (
                <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M1 6v16l7-4 8 4 7-4V2l-7 4-8-4-7 4z" />
                    <line x1="8" y1="2" x2="8" y2="18" />
                    <line x1="16" y1="6" x2="16" y2="22" />
                </svg>
            );
        case 'list':
            return (
                <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="8" y1="6" x2="21" y2="6" />
                    <line x1="8" y1="12" x2="21" y2="12" />
                    <line x1="8" y1="18" x2="21" y2="18" />
                    <line x1="3" y1="6" x2="3.01" y2="6" />
                    <line x1="3" y1="12" x2="3.01" y2="12" />
                    <line x1="3" y1="18" x2="3.01" y2="18" />
                </svg>
            );
        case 'pass':
            return (
                <svg width={size} height={size} viewBox="0 0 24 24" fill={active ? color : 'none'} stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="3" y="5" width="18" height="14" rx="2" ry="2" />
                    <path d="M9 12h6" />
                    <path d="M12 9v6" />
                </svg>
            );
        case 'saved':
            return (
                <svg width={size} height={size} viewBox="0 0 24 24" fill={active ? color : 'none'} stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z" />
                </svg>
            );
        case 'my':
            return (
                <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                    <circle cx="12" cy="7" r="4" />
                </svg>
            );
        default:
            return null;
    }
}

export default function BottomTabBar() {
    const pathname = usePathname();
    const t = useTranslation();

    return (
        <nav className={styles.tabBar} aria-label="Main Navigation">
            {TABS.map((tab) => {
                const isActive = pathname === tab.href || pathname.startsWith(tab.href + '/');
                const label = t(tab.labelKey);
                return (
                    <Link
                        key={tab.key}
                        href={tab.href}
                        className={`${styles.tabItem} ${isActive ? styles.active : ''}`}
                        aria-current={isActive ? 'page' : undefined}
                    >
                        <TabIcon tabKey={tab.key} active={isActive} />
                        <span className={styles.tabLabel}>{label}</span>
                    </Link>
                );
            })}
        </nav>
    );
}
