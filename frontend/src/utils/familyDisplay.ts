import type { TFunction } from 'i18next';

export interface FamilyReference {
  family_id?: number | null;
  family_name?: string | null;
}

export function formatFamilyNameWithId(family: FamilyReference, t: TFunction): string {
  const familyName = family.family_name?.trim();
  const familyId = family.family_id;

  if (familyName && familyId) {
    return t('families.display.name_with_id', { name: familyName, id: familyId });
  }

  if (familyName) {
    return familyName;
  }

  if (familyId) {
    return t('families.display.id_only', { id: familyId });
  }

  return t('families.display.unknown');
}

export function formatFamilyLabel(family: FamilyReference, t: TFunction): string {
  return t('families.display.label', { family: formatFamilyNameWithId(family, t) });
}
