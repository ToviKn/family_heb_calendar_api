import { apiClient } from './axios';
import type { DateConversionResponse, SimpleDate } from './types';

export interface ConvertHebrewParams extends SimpleDate {}

export interface ConvertGregorianParams extends SimpleDate {}

export async function convertGregorianToHebrew(params: ConvertHebrewParams): Promise<DateConversionResponse> {
  const { data } = await apiClient.get<DateConversionResponse>('/convert/hebrew', { params });
  return data;
}

export async function convertHebrewToGregorian(params: ConvertGregorianParams): Promise<DateConversionResponse> {
  const { data } = await apiClient.get<DateConversionResponse>('/convert/gregorian', { params });
  return data;
}

export async function getTodayConvertedDates(): Promise<DateConversionResponse> {
  const { data } = await apiClient.get<DateConversionResponse>('/convert/today');
  return data;
}
