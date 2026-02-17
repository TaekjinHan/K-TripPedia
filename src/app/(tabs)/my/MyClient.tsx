/**
 * MyClient -- 마이 탭 클라이언트 컴포넌트
 *
 * 내 리포트 수, 저장 수, 간단한 프로필 표시
 */
'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { supabase } from '@/lib/supabase';
import { ensureAnonSession } from '@/lib/auth';
import { getSavedPlaces } from '@/lib/savedSnapshot';
import styles from './MyClient.module.css';

interface MyStats {
    reportCount: number;
    savedCount: number;
}

export default function MyClient() {
    const [stats, setStats] = useState<MyStats>({ reportCount: 0, savedCount: 0 });
    const [userId, setUserId] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchStats = async () => {
            setLoading(true);
            const uid = await ensureAnonSession();
            setUserId(uid);

            // 로컬 스냅샷에서 저장 수
            const saved = getSavedPlaces();
            const savedCount = saved.length;

            // 서버에서 리포트 수
            let reportCount = 0;
            if (uid) {
                const { count } = await supabase
                    .from('observations')
                    .select('id', { count: 'exact', head: true })
                    .eq('user_id', uid);
                reportCount = count ?? 0;
            }

            setStats({ reportCount, savedCount });
            setLoading(false);
        };

        fetchStats();
    }, []);

    return (
        <div className={styles.container}>
            {/* 헤더 */}
            <div className={styles.header}>
                <h1 className={styles.title}>マイページ</h1>
            </div>

            {/* 프로필 카드 */}
            <div className={styles.profileCard}>
                <div className={styles.avatar}>
                    <svg width={40} height={40} viewBox="0 0 24 24" fill="none"
                        stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                        <circle cx="12" cy="8" r="4" />
                        <path d="M4 21c0-4.418 3.582-8 8-8s8 3.582 8 8" />
                    </svg>
                </div>
                <div className={styles.profileInfo}>
                    <span className={styles.profileName}>ゲストユーザー</span>
                    <span className={styles.profileId}>
                        {userId ? `ID: ${userId.slice(0, 8)}...` : '匿名'}
                    </span>
                </div>
            </div>

            {/* 통계 */}
            <div className={styles.statsRow}>
                <div className={styles.statCard}>
                    <span className={styles.statValue}>
                        {loading ? '-' : stats.reportCount}
                    </span>
                    <span className={styles.statLabel}>レポート</span>
                </div>
                <div className={styles.statCard}>
                    <span className={styles.statValue}>
                        {loading ? '-' : stats.savedCount}
                    </span>
                    <span className={styles.statLabel}>保存済み</span>
                </div>
            </div>

            {/* 메뉴 */}
            <div className={styles.menuSection}>
                <Link href="/saved" className={styles.menuItem}>
                    <span>保存済みリスト</span>
                    <svg width={16} height={16} viewBox="0 0 24 24" fill="none"
                        stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                        <polyline points="9 6 15 12 9 18" />
                    </svg>
                </Link>
                <Link href="/pass" className={styles.menuItem}>
                    <span>パスカード</span>
                    <svg width={16} height={16} viewBox="0 0 24 24" fill="none"
                        stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                        <polyline points="9 6 15 12 9 18" />
                    </svg>
                </Link>
            </div>

            {/* 버전 정보 */}
            <div className={styles.footer}>
                <p className={styles.version}>ひとりOK v0.1.0</p>
                <p className={styles.copyright}>hitori-ok.ksnackpedia.com</p>
            </div>
        </div>
    );
}
