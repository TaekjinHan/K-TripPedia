import { redirect } from 'next/navigation';

/**
 * 루트 페이지 -- 지도 탭으로 리다이렉트
 */
export default function Home() {
  redirect('/map');
}
