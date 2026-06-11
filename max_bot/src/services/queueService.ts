import { djangoClient } from '../api/djangoClient.js';
import type {
  SubscribeResult,
  TalonDetails,
  TalonListItem,
} from '../types/queue.js';

export async function subscribeToTalon(
  externalUserId: number,
  talonId: number,
): Promise<SubscribeResult> {
  const response = await djangoClient.post(
    '/api/internal/max/talons/subscribe/',
    {
      external_user_id: String(externalUserId),
      talon_id: talonId,
    },
  );

  return response.data as SubscribeResult;
}

export async function getMyTalons(
  externalUserId: number,
): Promise<TalonListItem[]> {
  const response = await djangoClient.get(
    '/api/internal/max/talons/',
    {
      params: {
        external_user_id: String(externalUserId),
      },
    },
  );

  return response.data.talons as TalonListItem[];
}

export async function getTalonDetails(
  externalUserId: number,
  talonId: number,
): Promise<TalonDetails> {
  const response = await djangoClient.get(
    `/api/internal/max/talons/${talonId}/`,
    {
      params: {
        external_user_id: String(externalUserId),
      },
    },
  );

  return response.data as TalonDetails;
}

export async function saveTalonComment(
  externalUserId: number,
  talonId: number,
  comment: string,
): Promise<TalonDetails> {
  const response = await djangoClient.post(
    `/api/internal/max/talons/${talonId}/comment/`,
    {
      external_user_id: String(externalUserId),
      comment,
    },
  );

  return response.data as TalonDetails;
}
