CELERY_BEAT_SCHEDULE = {

    "sync-every-5-minutes": {
        "task": "app.tasks.sync_vouchers",
        "schedule": 300,
    },

    "expire-vouchers": {
        "task": "app.tasks.expire_vouchers",
        "schedule": 60,
    },

}
