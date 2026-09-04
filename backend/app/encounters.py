"""Keep the shared fields of a photo encounter in one consistent state.

An observation is the canonical encounter record. Photos linked to it retain
their own file/EXIF data, but date, time, place and note are shared deliberately.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .models import Observation, UserPhoto


def sync_photos_from_observation(observation: Observation) -> None:
    """Copy the canonical encounter fields to every linked photo."""
    for photo in observation.photos:
        photo.profile_id = observation.profile_id
        photo.date = observation.date
        photo.time = observation.time
        photo.location_name = observation.location_name
        photo.caption = observation.notes
        photo.encounter_type = observation.encounter_type or "wild"
        photo.animal_sex = observation.animal_sex or "unknown"
        photo.measurement = observation.measurement
        photo.observed_weight = observation.observed_weight
        photo.photo_metadata = {
            **(photo.photo_metadata or {}),
            "encounter_type": observation.encounter_type or "wild",
        }


def sync_observation_from_photo(photo: UserPhoto) -> None:
    """Apply a photo edit to its observation and all sibling photos."""
    observation = photo.observation
    if observation is None:
        return
    observation.date = photo.date
    observation.time = photo.time
    observation.location_name = photo.location_name
    observation.notes = photo.caption
    observation.encounter_type = photo.encounter_type or "wild"
    observation.animal_sex = photo.animal_sex or "unknown"
    observation.measurement = photo.measurement
    observation.observed_weight = photo.observed_weight
    sync_photos_from_observation(observation)


def reconcile_linked_encounters(db: Session) -> int:
    """Gently align records created before photo encounters were unified.

    Existing observation values win. Missing values are filled from the oldest
    linked photo, then the result is copied to all photos in that encounter.
    """
    observations = db.execute(
        select(Observation)
        .where(Observation.photos.any())
        .options(selectinload(Observation.photos))
        .order_by(Observation.id)
    ).scalars()
    changed = 0
    for observation in observations:
        photos = sorted(observation.photos, key=lambda photo: photo.id)
        if not photos:
            continue
        source = photos[0]
        if observation.date is None:
            observation.date = source.date
        if observation.time is None:
            observation.time = source.time
        if not observation.location_name:
            observation.location_name = source.location_name
        if not observation.notes:
            observation.notes = source.caption
        if not observation.encounter_type:
            observation.encounter_type = source.encounter_type or "wild"
        if not observation.animal_sex:
            observation.animal_sex = source.animal_sex or "unknown"
        if not observation.measurement:
            observation.measurement = source.measurement
        if not observation.observed_weight:
            observation.observed_weight = source.observed_weight
        before = [
            (
                photo.profile_id, photo.date, photo.time, photo.location_name,
                photo.caption, photo.encounter_type, photo.animal_sex,
                photo.measurement, photo.observed_weight,
            )
            for photo in photos
        ]
        sync_photos_from_observation(observation)
        after = [
            (
                photo.profile_id, photo.date, photo.time, photo.location_name,
                photo.caption, photo.encounter_type, photo.animal_sex,
                photo.measurement, photo.observed_weight,
            )
            for photo in photos
        ]
        changed += int(before != after)
    return changed
