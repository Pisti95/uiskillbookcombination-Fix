import ui
import mouseModule
import player
import item
import types
import net
import uiToolTip
import chat
import localeInfo
import app

SKILLBOOK_SLOT_MAX = player.SKILLBOOK_COMB_SLOT_MAX # 10
INVENTORY_PAGE_SIZE = player.INVENTORY_PAGE_SIZE # 45
if app.WJ_SPLIT_INVENTORY_SYSTEM:
	SPECIAL_INVENTORY_PAGE_SIZE = player.SPECIAL_INVENTORY_PAGE_SIZE
USE_LIMIT_RANGE = 4000

SKILLBOOK_COMBI_UI_CLOSE = 0
SKILLBOOK_COMBI_UI_OPEN = 1
SKILLBOOK_COMBI_START = 2

class SkillBookCombinationWindow(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.inven = None
		if app.WJ_SPLIT_INVENTORY_SYSTEM:
			self.invenSpecial = None
		self.itemToolTip = uiToolTip.ItemToolTip()

	def __del__(self):
		ui.ScriptWindow.__del__(self)
		del self.inven
		if app.WJ_SPLIT_INVENTORY_SYSTEM:
			del self.invenSpecial
		del self.itemToolTip

	def Close(self):
		for index, key in self.SkillBookList.items():
			i = key[1] # attached inven pos
			self.SetCanMouseEventSlot(i)

		net.SendSkillBookCombinationPacket2(self.SkillBookList, SKILLBOOK_COMBI_UI_CLOSE)

		del self.SkillBookList
		del self.AcceptButton
		del self.CancelButton
		del self.Slot
		self.Hide()

	def Open(self):
		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "UIScript/SkillBookCombinationDialog2.py")
		except:
			import exception
			exception.Abort("SkillBookCombinationWindow.Open.SkillBookCombinationDialog2.py")

		try:
			## Title Bar Close Event
			self.GetChild("SkillBook_TitleBar").SetCloseEvent(ui.__mem_func__(self.Close))

			## Button Event
			self.AcceptButton = self.GetChild("accept_button")
			self.CancelButton = self.GetChild("cancel_button")
			self.AcceptButton.SetEvent(ui.__mem_func__(self.ClickAcceptButton))
			self.CancelButton.SetEvent(ui.__mem_func__(self.Close))

			## SkillBook Slot
			Slot = self.GetChild("SkillBookSlot")
			Slot.SetSelectEmptySlotEvent(ui.__mem_func__(self.SelectEmptySlot)) ## [Event] 빈 슬롯 Click 할 때
			Slot.SetSelectItemSlotEvent(ui.__mem_func__(self.SelectItemSlot)) ## [Event] 슬롯 안에 있는 Item Click 할 때
			Slot.SetOverInItemEvent(ui.__mem_func__(self.OverInItem))
			Slot.SetOverOutItemEvent(ui.__mem_func__(self.OverOutItem))
			self.Slot = Slot

			self.SkillBookList = {}

			(self.StartPosX, self.StartPosY, z) = player.GetMainCharacterPosition()

			net.SendSkillBookCombinationPacket2(self.SkillBookList, SKILLBOOK_COMBI_UI_OPEN)

			self.SetTop()
		except:
			import exception
			exception.Abort("SkillBookCombinationWindow.Open.Child")

	def OverInItem(self, slotIndex):
		if not self.itemToolTip:
			return

		invenPos = self.SkillBookList[slotIndex][1]

		if app.ENABLE_EXTEND_INVEN_SYSTEM:
			if app.WJ_SPLIT_INVENTORY_SYSTEM:
				##if 0 <= invenPos < (INVENTORY_PAGE_SIZE * 28):
				if 0 <= invenPos < (INVENTORY_PAGE_SIZE * player.INVENTORY_PAGE_COUNT) + player.SKILL_BOOK_INVENTORY_SLOT_COUNT:
					self.itemToolTip.SetInventoryItem(invenPos, player.INVENTORY)
			else:
				if 0 <= invenPos < (INVENTORY_PAGE_SIZE * player.INVENTORY_PAGE_COUNT):
					self.itemToolTip.SetInventoryItem(invenPos, player.INVENTORY)
		else:
			if -1 < invenPos < INVENTORY_PAGE_SIZE * 2:
				self.itemToolTip.SetInventoryItem(invenPos, player.INVENTORY)
				
				

	def OverOutItem(self):
		if not self.itemToolTip:
			return

		self.itemToolTip.HideToolTip()

	## Inventory -> SkillBook Combination Grid Slot
	def SelectEmptySlot(self, slotIndex):
		## 마우스에 아이템이 붙어 있어야 함
		if not mouseModule.mouseController.isAttached():
			return

		attachedSlotType = mouseModule.mouseController.GetAttachedType()
		attachedSlotPos = mouseModule.mouseController.GetAttachedSlotNumber()
		attachedItemVnum = player.GetItemIndex(attachedSlotPos)
		item.SelectItem(attachedItemVnum)

		itemType = item.GetItemType()

		if app.WJ_SPLIT_INVENTORY_SYSTEM:
			if (player.SLOT_TYPE_INVENTORY != attachedSlotType and player.SLOT_TYPE_SKILL_BOOK_INVENTORY != attachedSlotType ):
				return

			if attachedSlotPos >= (player.ITEM_SLOT_COUNT + player.SKILL_BOOK_INVENTORY_SLOT_COUNT):
				return
		else:
			if player.SLOT_TYPE_INVENTORY != attachedSlotType:
				return

			if attachedSlotPos >= player.ITEM_SLOT_COUNT:
				return

		if itemType != item.ITEM_TYPE_SKILLBOOK:
			return

		for index, key in self.SkillBookList.items():
			if attachedSlotPos == key[1]:
				return

		mouseModule.mouseController.DeattachObject()

		self.SkillBookList[slotIndex] = (attachedSlotType, attachedSlotPos, 1)
		self.Slot.SetItemSlot(slotIndex, attachedItemVnum)
		self.Slot.RefreshSlot()

	def SelectItemSlot(self, slotIndex):
		if mouseModule.mouseController.isAttached():
			return

		self.SetCanMouseEventSlot(self.SkillBookList[slotIndex][1])

		## 범위 안
		if -1 < slotIndex < SKILLBOOK_SLOT_MAX:
			self.ClearSlot(slotIndex)
			self.Slot.RefreshSlot()
		else:
			pass

	def ClearSlot(self, idx):
		del self.SkillBookList[idx]
		self.Slot.ClearSlot(idx)

	def SetCanMouseEventSlot(self, idx):
		if not isinstance(idx, types.NoneType):
			if app.WJ_SPLIT_INVENTORY_SYSTEM:
				if self.inven or self.invenSpecial:
					page = self.inven.GetInventoryPageIndex() # range 0 ~ 1
					special_page = self.invenSpecial.GetInventoryPageIndex()
					
					if (page * INVENTORY_PAGE_SIZE) <= idx < ((page + 1) * INVENTORY_PAGE_SIZE): # range 0 ~ 44, 45 ~ 89
						idx = idx - (page * INVENTORY_PAGE_SIZE)
						self.inven.wndItem.SetCanMouseEventSlot(idx)

					elif self.invenSpecial.GetInventoryType() == 0:
						if (item.SKILL_BOOK_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE)) <= idx < (item.SKILL_BOOK_INVENTORY_SLOT_START + (((special_page + 1) * SPECIAL_INVENTORY_PAGE_SIZE))):
							idx = idx - (item.SKILL_BOOK_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE))
							self.invenSpecial.wndItem.SetCanMouseEventSlot(idx)

			else:
				if idx >= INVENTORY_PAGE_SIZE:
					if app.ENABLE_EXTEND_INVEN_SYSTEM:
						page = self.inven.GetInventoryPageIndex() # 0,1,2,3
						idx -= (page * INVENTORY_PAGE_SIZE)
					else:
						idx -= INVENTORY_PAGE_SIZE

				self.inven.wndItem.SetCanMouseEventSlot(idx)

	def ClickAcceptButton(self):
		cnt = 0
		for i in self.SkillBookList:
			if not isinstance(i, types.NoneType):
				cnt += 1

		if cnt != SKILLBOOK_SLOT_MAX:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.COMB_NOT_FULL_BOOK)
			return

		net.SendSkillBookCombinationPacket2(self.SkillBookList, SKILLBOOK_COMBI_START)

		for index, key in self.SkillBookList.items():
			i = key[1] # attached inven pos
			self.SetCanMouseEventSlot(i)

		for i in xrange(SKILLBOOK_SLOT_MAX):
			self.ClearSlot(i)

		self.Slot.RefreshSlot()

	def SetInven(self, inven):
		self.inven = inven
		
	if app.WJ_SPLIT_INVENTORY_SYSTEM:
		def SetSpecialInven(self, invenSpecial):
			self.invenSpecial = invenSpecial

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def OnUpdate(self):
		if app.WJ_SPLIT_INVENTORY_SYSTEM:
			if not self.inven or not self.invenSpecial:
				return
		else:
			if not self.inven:
				return
	
		page = self.inven.GetInventoryPageIndex() # range 0 ~ 1
		if app.WJ_SPLIT_INVENTORY_SYSTEM:
			special_page = self.invenSpecial.GetInventoryPageIndex()
	
		if not self.SkillBookList:
			return
	
		for index, key in self.SkillBookList.items():
			if not isinstance(key, types.NoneType):
				i = key[1] # attached inven pos
				if (page * INVENTORY_PAGE_SIZE) <= i < ((page + 1) * INVENTORY_PAGE_SIZE): # range 0 ~ 44, 45 ~ 89
					lock_idx = i - (page * INVENTORY_PAGE_SIZE)
					self.inven.wndItem.SetCantMouseEventSlot(lock_idx)
					
				if app.WJ_SPLIT_INVENTORY_SYSTEM:
					if self.invenSpecial.GetInventoryType() == 0:
						if (item.SKILL_BOOK_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE)) <= i < (item.SKILL_BOOK_INVENTORY_SLOT_START + (((special_page + 1) * SPECIAL_INVENTORY_PAGE_SIZE))):
							lock_idx = i - (item.SKILL_BOOK_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE))
							self.invenSpecial.wndItem.SetCantMouseEventSlot(lock_idx)
	
			else:
				continue
	
		(x, y, z) = player.GetMainCharacterPosition()
		if abs(x - self.StartPosX) > USE_LIMIT_RANGE or abs(y - self.StartPosY) > USE_LIMIT_RANGE:
			self.Close()
			
