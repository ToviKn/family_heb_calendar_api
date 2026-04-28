import { apiClient } from './axios';
import type { DateConversionResponse, SimpleDate } from './types';

export interface GregorianDateParams extends SimpleDate {}

export interface HebrewDateParams extends SimpleDate {}

export async function convertGregorianToHebrew(params: GregorianDateParams): Promise<DateConversionResponse> {
  const { data } = await apiClient.get<DateConversionResponse>('/convert/hebrew', { params });
  return data;
}

export async function convertHebrewToGregorian(params: HebrewDateParams): Promise<DateConversionResponse> {
  const { data } = await apiClient.get<DateConversionResponse>('/convert/gregorian', { params });
  return data;
}

export async function getTodayConvertedDates(): Promise<DateConversionResponse> {
  const { data } = await apiClient.get<DateConversionResponse>('/convert/today');
  return data;
}
