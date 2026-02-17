'use server';

import { POINT_VALUES, normalizeTotalPoints } from '@/lib/points';
import { createServiceRoleClient } from '@/lib/supabaseServer';

export type SubmitReportErrorCode = 'ALREADY_SUBMITTED_TODAY' | 'UNKNOWN';

export interface SubmitReportPayload {
    userId: string;
    placeId: string;
    soloOutcome: string;
    seatType?: string | null;
    staffReaction?: string | null;
    mealPeriod?: string | null;
    memo?: string | null;
}

export interface SubmitReportResult {
    ok: boolean;
    pointsGranted: number;
    totalPoints: number;
    error?: string;
    errorCode?: SubmitReportErrorCode;
}

interface PostgresErrorLike {
    code?: string;
    message?: string;
    details?: string | null;
    constraint?: string;
}

function isPostgresErrorLike(error: unknown): error is PostgresErrorLike {
    return typeof error === 'object' && error !== null;
}

function isDuplicateReportError(error: unknown): boolean {
    if (!isPostgresErrorLike(error) || error.code !== '23505') {
        return false;
    }

    const source = `${error.constraint ?? ''} ${error.message ?? ''} ${error.details ?? ''}`;
    return source.includes('observations_user_place_observed_unique');
}

export async function submitReportAction(
    payload: SubmitReportPayload,
): Promise<SubmitReportResult> {
    let observationIdForRollback: string | null = null;

    try {
        const supabase = createServiceRoleClient();

        const normalizedMemo = payload.memo?.trim() || null;
        const pointsGranted = POINT_VALUES.report;

        const observedAt = new Date().toISOString().slice(0, 10);

        const { data: existingReports, error: duplicateCheckError } = await supabase
            .from('observations')
            .select('id')
            .eq('user_id', payload.userId)
            .eq('place_id', payload.placeId)
            .eq('observed_at', observedAt)
            .eq('source_type', 'USER_VISIT')
            .limit(1);

        if (duplicateCheckError) {
            throw duplicateCheckError;
        }

        if ((existingReports ?? []).length > 0) {
            return {
                ok: false,
                pointsGranted: 0,
                totalPoints: 0,
                errorCode: 'ALREADY_SUBMITTED_TODAY',
                error: 'Duplicate report for same place and day',
            };
        }

        const { data: observation, error: observationError } = await supabase
            .from('observations')
            .insert({
                place_id: payload.placeId,
                user_id: payload.userId,
                source_type: 'USER_VISIT',
                observed_at: observedAt,
                solo_outcome: payload.soloOutcome,
                seat_type: payload.seatType || null,
                staff_reaction: payload.staffReaction || null,
                meal_period: payload.mealPeriod || null,
                memo_short: normalizedMemo,
            })
            .select('id')
            .single();

        if (observationError || !observation) {
            throw observationError ?? new Error('Failed to create observation');
        }

        const observationId = observation.id as string;
        observationIdForRollback = observationId;

        const { error: pointEventError } = await supabase.from('point_events').insert({
            user_id: payload.userId,
            event_type: 'report',
            entity_type: 'observation',
            entity_id: observationId,
            points: pointsGranted,
        });

        if (pointEventError) {
            await supabase.from('observations').delete().eq('id', observationId);
            throw pointEventError;
        }

        const { data: dailyRow } = await supabase
            .from('user_stats_daily')
            .select('points,reports_count,confirmed_count')
            .eq('user_id', payload.userId)
            .eq('stat_date', observedAt)
            .maybeSingle();

        const nextDailyPoints = (dailyRow?.points ?? 0) + pointsGranted;
        const nextReportsCount = (dailyRow?.reports_count ?? 0) + 1;

        const { error: dailyUpsertError } = await supabase
            .from('user_stats_daily')
            .upsert(
                {
                    user_id: payload.userId,
                    stat_date: observedAt,
                    points: nextDailyPoints,
                    reports_count: nextReportsCount,
                    confirmed_count: dailyRow?.confirmed_count ?? 0,
                },
                { onConflict: 'user_id,stat_date' },
            );

        if (dailyUpsertError) {
            throw dailyUpsertError;
        }

        const { data: totalPointsRaw, error: pointSumError } = await supabase.rpc(
            'get_user_total_points',
            {
                target_user_id: payload.userId,
            },
        );

        if (pointSumError) {
            throw pointSumError;
        }

        const totalPoints = normalizeTotalPoints(Number(totalPointsRaw ?? 0));

        observationIdForRollback = null;

        return {
            ok: true,
            pointsGranted,
            totalPoints,
        };
    } catch (error) {
        try {
            if (observationIdForRollback) {
                const rollbackClient = createServiceRoleClient();
                await rollbackClient
                    .from('observations')
                    .delete()
                    .eq('id', observationIdForRollback);
            }
        } catch (rollbackError) {
            console.error('[submitReportAction] rollback failed:', rollbackError);
        }

        const duplicateToday = isDuplicateReportError(error);

        console.error('[submitReportAction] failed:', error);
        return {
            ok: false,
            pointsGranted: 0,
            totalPoints: 0,
            errorCode: duplicateToday ? 'ALREADY_SUBMITTED_TODAY' : 'UNKNOWN',
            error: duplicateToday
                ? 'Duplicate report for same place and day'
                : error instanceof Error
                    ? error.message
                    : 'Unknown error',
        };
    }
}
