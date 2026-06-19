import { djangoClient } from '../api/djangoClient.js'
import type {
  MaxHelper,
  MaxHelperLinkResult,
  MaxHelpRequest,
} from '../types/helper.js'

function normalizeHelper(data: any): MaxHelper {
  return (data.helper ?? data) as MaxHelper
}

export async function linkHelper(
  externalUserId: number,
  code: string,
): Promise<MaxHelperLinkResult> {
  const response = await djangoClient.post(
    '/api/internal/max/helpers/link/',
    {
      external_user_id: String(externalUserId),
      code,
    },
  )

  return response.data as MaxHelperLinkResult
}

export async function getHelper(
  externalUserId: number,
): Promise<MaxHelper> {
  const response = await djangoClient.get(
    '/api/internal/max/helpers/me/',
    {
      params: {
        external_user_id: String(externalUserId),
      },
    },
  )

  return normalizeHelper(response.data)
}

export async function toggleHelperActive(
  externalUserId: number,
): Promise<MaxHelper> {
  const response = await djangoClient.post(
    '/api/internal/max/helpers/toggle-active/',
    {
      external_user_id: String(externalUserId),
    },
  )

  return normalizeHelper(response.data)
}

export async function getHelperRequests(
  externalUserId: number,
): Promise<MaxHelpRequest[]> {
  const response = await djangoClient.get(
    '/api/internal/max/helpers/requests/',
    {
      params: {
        external_user_id: String(externalUserId),
      },
    },
  )

  return response.data.requests as MaxHelpRequest[]
}

export async function completeHelperRequest(
  externalUserId: number,
  requestId: number,
): Promise<{ detail: string }> {
  const response = await djangoClient.post(
    `/api/internal/max/helpers/requests/${requestId}/complete/`,
    {
      external_user_id: String(externalUserId),
    },
  )

  return response.data as { detail: string }
}