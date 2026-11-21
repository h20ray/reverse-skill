# 04 — Laravel Backend Integration Guide

This guide details the database schemas, Eloquent models, API endpoints, and Tamagotchi evolution services for Bongo Cat in Laravel.

---

## 1. Database Schema & Migration

In Niskala, `attendance_streak_pets` already contains a JSON column `outfits`. If creating a new migration or verifying:

```php
Schema::table('attendance_streak_pets', function (Blueprint $table) {
    if (!Schema::hasColumn('attendance_streak_pets', 'outfits')) {
        $table->json('outfits')->nullable()->after('stage');
    }
    if (!Schema::hasColumn('attendance_streak_pets', 'unlocked_skins')) {
        $table->json('unlocked_skins')->nullable()->after('outfits');
    }
    if (!Schema::hasColumn('attendance_streak_pets', 'coins')) {
        $table->unsignedInteger('coins')->default(0)->after('total_exp');
    }
});
```

### JSON Structure of `outfits`
```json
{
  "skin": "Cat",
  "hat": "BlackWizardHat",
  "emote": "FaceHeartSmileEmoji"
}
```

---

## 2. Eloquent Model (`AttendanceStreakPet.php`)

In `app/Models/AttendanceStreakPet.php`:

```php
namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class AttendanceStreakPet extends Model
{
    protected $table = 'attendance_streak_pets';

    protected $fillable = [
        'user_id',
        'pet_name',
        'pet_type',
        'current_streak',
        'longest_streak',
        'total_exp',
        'coins',
        'level',
        'stage',
        'outfits',
        'unlocked_skins',
        'last_clock_in_date',
        'last_interaction_at',
    ];

    protected $casts = [
        'id' => 'integer',
        'user_id' => 'integer',
        'current_streak' => 'integer',
        'longest_streak' => 'integer',
        'total_exp' => 'integer',
        'coins' => 'integer',
        'level' => 'integer',
        'outfits' => 'array',
        'unlocked_skins' => 'array',
        'last_clock_in_date' => 'date:Y-m-d',
        'last_interaction_at' => 'datetime',
    ];

    /**
     * Default outfit fallback
     */
    public function getOutfitsAttribute($value): array
    {
        $decoded = is_string($value) ? json_decode($value, true) : $value;
        return array_merge([
            'skin' => 'Cat',
            'hat' => null,
            'emote' => 'FaceHeartSmileEmoji',
        ], $decoded ?: []);
    }
}
```

---

## 3. Controller API Endpoints

In `app/Modules/Attendance/Controllers/StreakPetController.php`:

```php
namespace App\Modules\Attendance\Controllers;

use App\Http\Controllers\Controller;
use App\Modules\Attendance\Services\BongoGrowthService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class StreakPetController extends Controller
{
    /**
     * Update equipped Bongo Cat outfit (Wardrobe)
     */
    public function updateOutfit(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'outfit.skin' => 'required|string|max:100',
            'outfit.hat' => 'nullable|string|max:100',
            'outfit.emote' => 'nullable|string|max:100',
        ]);

        $pet = $request->user()->attendanceStreakPet;
        if (!$pet) {
            return response()->json(['status' => false, 'message' => 'Pet not found'], 404);
        }

        $pet->update([
            'outfits' => $validated['outfit'],
        ]);

        return response()->json([
            'status' => true,
            'message' => 'Outfit updated successfully',
            'data' => $pet->fresh(),
        ]);
    }

    /**
     * Buy item with Attendance Coins
     */
    public function buyItem(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'item_id' => 'required|string',
            'item_type' => 'required|in:hat,emote',
            'price' => 'required|integer|min:0',
        ]);

        $pet = $request->user()->attendanceStreakPet;
        if ($pet->coins < $validated['price']) {
            return response()->json(['status' => false, 'message' => 'Insufficient coins'], 422);
        }

        $pet->decrement('coins', $validated['price']);

        return response()->json([
            'status' => true,
            'message' => 'Item purchased successfully',
            'coins_remaining' => $pet->coins,
        ]);
    }
}
```

---

## 4. Tamagotchi Evolution Service

See full algorithm and growth timeline in [**`docs/07-TAMAGOTCHI-GROWTH-CHART-AND-COIN-ECONOMY.md`**](./07-TAMAGOTCHI-GROWTH-CHART-AND-COIN-ECONOMY.md).
