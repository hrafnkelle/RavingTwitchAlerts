$header = @{
    "Authorization"="Bearer $env:TWITCH_BEARER_OAUTH"
    "Content-Type"="application/json"
    "Client-ID"="$env:TWITCH_CLIENT_ID"
} 

$body = @"
{
    "type": "channel.channel_points_custom_reward_redemption.add",
    "version": "1",
    "condition": {
        "broadcaster_user_id": "$env:IRC_OWNER"
    },
    "transport": {
        "method": "webhook",
        "callback": "$env:TWITCH_URL/webhooks/callback",
        "secret": "$env:TWITCH_CLIENT_SECRET"
    }
}
"@

Invoke-WebRequest -UseBasicParsing -Method POST -Headers $header -Body $body -Uri https://api.twitch.tv/helix/eventsub/subscriptions