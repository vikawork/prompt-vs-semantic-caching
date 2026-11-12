FennelBox support manual

This manual describes FennelBox, an invented household status display used only in this measurement. It does not describe an available product or a real company. The display shows reminders, room readings, and delivery notes entered by the household. It is not a security alarm, a medical monitor, or an emergency communication device. Its support rules below are the complete rules for this fictional product. When answering a question, use the applicable rule and state any condition that changes the answer. A feature not described here must not be assumed to exist.

1. Power and placement

FennelBox uses the supplied twelve-volt adapter and has no rechargeable battery. Place it on a dry, level indoor shelf with a hand's width of clear space behind the ventilation grille. A switched socket is acceptable, but switching it off interrupts reminders and network synchronization. Do not connect a different adapter merely because its plug fits. Disconnect power before moving the unit. The small amber lamp indicates incoming power; it does not prove that the display has finished starting. A cracked adapter, a frayed cable, or a hot connector requires immediate disconnection and a support request.

2. First setup

Initial setup takes place on the display itself. Select a language, choose the local time zone, and create the owner profile with a passphrase of at least twelve characters. The setup screen then offers a wireless connection and a short display test. Network setup may be skipped, but account recovery and remote synchronization remain unavailable until a connection is added. Write down the recovery code before leaving the setup screen. The code is shown once and is not sent by email. Finishing the display test creates a local welcome reminder; it does not start a paid subscription.

3. Network connection

The unit supports two-point-four-gigahertz wireless networks with a password. It does not support five-gigahertz-only networks, wired Ethernet, captive sign-in pages, or enterprise certificate authentication. To change networks, open Settings, then Connection, then Choose network. Previously entered readings remain on the display during the change. A connection test checks the wireless link and the synchronization service separately. A successful wireless check with a failed synchronization check usually means the device has a local connection but cannot reach the service. Do not erase the household to troubleshoot that condition; first retry the connection test and verify the network password.

4. Working without a connection

Local reminders and the most recently synchronized readings remain available offline for thirty days. The display marks remote readings with their last update time so an old reading is not presented as current. New local entries are queued until the connection returns. Remote changes made elsewhere are not visible while the unit is offline. After thirty days without synchronization, local reminders still work, but remote-reading tiles are hidden until a successful connection. Disconnecting the network never upgrades a plan, cancels a plan, or changes the household's billing status. Check those settings separately if an offline period overlaps a renewal.

5. Restart and reset

A restart preserves profiles, reminders, and network settings. Hold the side button for three seconds and choose Restart. A factory reset is different: Settings, then Household, then Erase household removes all local profiles, saved readings, reminders, and network credentials. It requires the owner passphrase and a second confirmation. A reset does not cancel a subscription or erase a cloud archive. Export wanted data and request cloud deletion separately before transferring or recycling the display. If the screen is frozen, disconnect power for twenty seconds, reconnect it, and allow the startup test to finish before attempting a reset.

6. Data export formats

Version three exports readings and reminder history as a comma-separated-values file. PDF export is not supported. The file uses a header row, explicit units, and timestamps that include the selected time zone. Notes containing commas are quoted so a spreadsheet can import them without moving text into another column. Exports are available from Settings, then Data, then Export. Choose a destination removable drive before starting. The display reports completion only after the file has been written and checked. Removing the drive while the progress indicator is moving can leave an incomplete file; repeat the export rather than trusting that file.

7. Export date range

Each export may cover up to ninety consecutive days. A longer archive must be exported as several nonoverlapping date ranges. Start and end dates are inclusive, and the export preview states the number of calendar days selected. Choosing a date range does not restore records already removed under the retention rule. The preview shows the earliest record still available before it offers the export button. If a household changes its time zone, existing events keep their original recorded times; the file also includes a normalized ordering field. This avoids silently changing an old reminder's date during a later export.

8. Household profiles

One display supports an owner profile and up to five additional household profiles, for six profiles in total. Profiles have separate reminder lists but share the display's network and clock settings. Only the owner may add profiles, change billing, request an archive deletion, or reset the household. A profile may be renamed without changing its reminders. Deleting an additional profile removes its local reminder list after confirmation; it does not remove other profiles. The owner profile cannot be deleted alone. To remove the owner, transfer ownership to another existing profile or erase the whole household through the factory-reset procedure.

9. Guest access

Guest mode displays only the shared notice board and the current clock. It does not expose private reminders, billing information, exports, or diagnostic attachments. The owner enables guest mode from Settings, then Access, and can set it to expire after one day, one week, or a manually chosen time. A guest cannot create another guest, change the expiry, or approve a software update. Leaving guest mode requires the owner passphrase. Guest mode is useful when a display is placed in a shared room, but it is not a substitute for physically protecting the unit from unauthorized handling.

10. Quiet hours

Quiet hours run from ten at night until seven in the morning unless the owner changes them. During that interval the display dims and ordinary reminder sounds are suppressed. A reminder marked urgent still appears visually but does not bypass quiet hours with a sound. Quiet hours are interpreted in the device's selected local time zone. Changing the time zone can therefore change the next quiet interval. The test button previews the configured brightness and sound behavior without waiting for night. Quiet hours affect the display only; they do not cancel messages already queued for email delivery under the separate notification settings.

11. Email notifications

Email notifications are optional and are off after initial setup. The owner can enable a daily digest, immediate reminder notices, or both. Each destination address must be verified before messages are sent. To stop notification emails, open Settings, then Notifications, and disable both switches. Turning off only the daily digest leaves immediate notices enabled. Delivery failures appear in the notification history without exposing the full destination address on the shared screen. The system makes two retry attempts and then stops that message. Repeated failed delivery never causes an account lockout or changes the reminder's local due time.

12. Plans and upgrades

The basic plan includes local reminders, one connected display, and thirty days of synchronized history. The plus plan adds longer history and a second connected display. An upgrade takes effect immediately after the owner confirms the displayed charge. The confirmation screen states the remaining billing period and any prorated amount before accepting payment. A downgrade takes effect at the next renewal, preserving current access until then. Data beyond the basic retention limit is not immediately erased at the downgrade request; the owner receives an export reminder before the new limit takes effect. Additional household profiles do not each require a separate paid plan.

13. Pausing service

A plus subscription may be paused for one billing month, at most twice in a calendar year. A pause begins at the next renewal rather than immediately. During a pause, local features continue and remote synchronization is suspended. The account page shows the pause start, the planned restart date, and the next charge date before confirmation. A pause does not extend a hardware warranty. The owner may cancel a scheduled pause before it starts, or end an active pause early; an early restart begins a new paid period after a separate charge confirmation. A yearly pause is not available.

14. Cancellation

Cancel a subscription from Account, then Plan, then Cancel renewal. Cancellation stops the next automatic renewal and preserves paid features until the current paid period ends. Canceling a hardware order is a different action found under Account, then Orders. An order can be canceled without a cancellation fee only before dispatch. Once dispatched, the order must follow the return process after delivery. Neither deleting the mobile companion nor resetting the display cancels a subscription. The cancellation confirmation identifies whether it concerns an order or a subscription, and the owner should retain that confirmation until the corresponding charge or shipment is resolved.

15. Renewal and payment

Monthly plans renew on the same calendar day each month. If that day does not exist in a later month, renewal occurs on that month's final day. Annual billing is available and renews on the anniversary date. Renewal notices are sent seven days before annual charges and one day before monthly charges. A failed payment receives a seven-day grace period, during which existing local features continue. The account page accepts a replacement payment card without requiring a new household. Updating a card does not itself retry an old charge; the owner must confirm the Retry payment action on the failed invoice.

16. Refund window

The first subscription purchase may be refunded within thirty calendar days, measured from the payment date. Later renewals are refundable only when a duplicate charge or a documented service billing error occurred. A refund request must identify the invoice and the reason; canceling renewal alone does not submit that request. Approved refunds return to the original payment method. Support cannot redirect a refund to a different card or issue store credit instead. The account page shows the refund status and the date it was sent to the payment processor. A completed processor handoff is not a promise about the bank's posting date.

17. Hardware returns

Unopened hardware may be returned within thirty days after delivery. Opened hardware is not eligible for a change-of-mind return, although a fault or delivery damage can still qualify for the separate repair or damage process. Keep the packaging until the delivery check is complete. A return must include the display, its adapter, and any supplied stand. Erase local household data before packing a unit that can still be operated. If a fault prevents erasure, state that in the request so the receiving team follows the data-handling procedure. A subscription cancellation does not automatically authorize a hardware return.

18. Return labels

For an approved unopened return, support provides a prepaid return label through the account's order page. The label expires fourteen days after issue. It is tied to the approved order and must not be reused for another unit or another shipment. Print it clearly and cover old shipping labels before handing the parcel to the carrier. Keep the carrier receipt until the return status changes to Received. An expired label can be replaced by support while the underlying return authorization remains valid. Do not send a parcel to an address found on an old invoice; the current label supplies the correct receiving destination.

19. Warranty coverage

The hardware warranty lasts twenty-four months from delivery. It covers manufacturing faults in the display and supplied adapter under normal indoor use. It does not cover liquid damage, outdoor exposure, unauthorized repairs, or damage from an incompatible power supply. Proof of the original delivery date is required, but an account order record is sufficient. A replacement supplied under warranty keeps the original warranty end date or receives ninety days of coverage, whichever is later. The warranty does not promise uninterrupted network service, preserve unsaved reminders after physical damage, or include a paid subscription. Those matters follow their own rules.

20. Ownership and warranty transfer

The remaining hardware warranty may transfer to a new owner once. The previous owner must remove the display from the household, erase local data, and provide the order reference through the transfer screen. The new owner then registers the unit and receives the remaining coverage date. Subscription benefits and stored cloud history do not transfer with the hardware. A personal software licence may transfer with the unit, but a team licence remains with its original team and cannot be reassigned through a hardware transfer. A second ownership transfer is possible for the hardware itself, but does not carry the warranty again.

21. Replacement parts

Lost adapters and stands are sold as replacement parts; loss is not a warranty fault. The parts page lists the adapter separately from the stand so the owner can order the correct item. A replacement charger is not offered because the unit has no battery and does not charge from a charger. If the display reports unstable power, first inspect the supplied adapter and cable for damage. Support may ask for the adapter's printed part code, but never for a household passphrase or recovery code. A suspected damaged adapter should remain disconnected until an approved replacement arrives.

22. Support availability

Text support is available every day from eight in the morning until eight in the evening, using the account's selected local time zone. Phone support is included only with the plus plan and is available on weekdays during the same hours. Basic-plan users can submit text requests without purchasing an upgrade. Requests submitted outside opening hours remain queued and receive a visible receipt number. The queue does not provide emergency monitoring. For an urgent electrical hazard, disconnect the unit safely instead of waiting for a response. Changing a device's time zone does not reorder or erase an already submitted support request.

23. Delivery and tracking

Standard delivery is estimated at three to five business days after dispatch. The order page shows dispatch separately from payment confirmation, because a paid order may still be awaiting packing. Tracking becomes available when the carrier first scans the parcel. A label-created status without a carrier scan does not prove that the carrier has the package. A delivery-date change may be requested before dispatch. After dispatch, use the carrier options linked from the order page; support cannot promise that a reroute will succeed. A requested date is not confirmed until the order page explicitly records the accepted date.

24. Damage and missing parcels

Report visible delivery damage within seven days of receipt, with a description and photographs of the packaging and affected part. Do not power on a visibly damaged unit. A parcel marked delivered but not found follows a missing-parcel investigation instead. First check the delivery location recorded by the carrier, then open a request from the order page. Damage and non-delivery requests use different forms because one concerns a received item and the other concerns an unlocated shipment. Neither form requires the household passphrase. Keep the original packaging during a damage investigation unless support explicitly authorizes disposal.

25. Collection locations

Collection is available in the invented service area Northport. The invented service area Southport receives delivery only and has no collection point. Choose collection before paying so the order carries the correct handling instruction. A Ready for collection notice is required before traveling to a collection point. The notice contains a collection code that may be shared with an authorized collector; it is not a device recovery code. Collection orders are held for ten days. After that period, an uncollected order is canceled and refunded to the original payment method after the returned stock is checked.

26. Software versions

Version two supports local reminders but has no data-export feature. Version three adds CSV export and improved offline status labels. Updates are free for compatible hardware and require owner approval. An update checks available space and power before installation, then restarts the display once. Do not disconnect power while the installation screen is visible. A failed download leaves the installed version unchanged and may be retried later. After a successful update, Settings, then About shows the installed version and installation date. Installing an update does not change the subscription price or renew an expired hardware warranty.

27. Storage and retention

The display retains up to ten thousand local history entries. When that limit is reached, the oldest completed history entries are removed first. Active reminders are not removed merely to make room for old readings. Basic-plan synchronized history is retained for thirty days; plus-plan history is retained for one year. An export is a separate file and is not later altered by these retention rules. Available storage appears in Settings, then Data. If space runs low, remove completed local history or export it before deletion. A factory reset is unnecessary when ordinary history cleanup frees enough space.

28. Cloud deletion

The owner can request cloud-archive deletion from Account, then Privacy. Confirmation starts a thirty-day recovery window, during which the request may be canceled from the same page. At the end of that window the archive is deleted and cannot be restored through support. Local records on an offline display are not erased by a cloud request; erase them on the device separately. Canceling a subscription does not submit an archive-deletion request. Removing an additional profile likewise does not delete the entire household archive. Export anything that must be retained before the deletion window ends, and store the export in a location the household controls.

29. Cleaning and safe use

Disconnect power and use a dry, soft cloth for routine cleaning. For a stubborn mark, slightly dampen the cloth with water and keep moisture away from ports and vents. Never spray the display directly, immerse it, or use abrasive cleaners. The product is rated for indoor use only and should not be placed outdoors even under a roof. Keep it away from cooking steam, open flames, and direct splashes. Reconnect power only after the surface is dry. A cleaning attempt does not require deleting data, changing the network, or opening the case. Opening the case is not a supported maintenance step.

30. Diagnostic codes

Code N1 means the wireless connection is unavailable; rerun the connection test before changing any account settings. Code S2 means synchronization is delayed while local reminders remain active. Code P3 means the power check failed and the unit should be disconnected for an adapter inspection. A diagnostic bundle contains version information, event times, and error codes, but excludes reminder text by default. The owner can inspect the bundle before attaching it to a support request. Support may request that bundle and the order reference. It will never require the household passphrase, recovery code, or a complete export of private reminders.
